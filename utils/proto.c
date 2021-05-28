#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <byteswap.h>

#include "mbedtls/ecdh.h"
#include "mbedtls/entropy.h"
#include "mbedtls/ctr_drbg.h"
#include "mbedtls/md5.h"
#include "mbedtls/platform.h"
#include "mbedtls/gcm.h"
#include "lz4.h"


#define rotr(x, n) ((x >> n) | (x << (32 - n)))  // x, n should be in ()


typedef struct uma_request
{
    unsigned int pre_size;
    char server_pub_key[32];
    char auth_data[20];
    char session_id[16];
    char cert_uuid[16];
    char random_bytes[32];
    char auth_key[50];
    char data[0];
} uma_request;


typedef struct uma_request_enc
{
    unsigned int size;
    char client_pubkey[32];
    char aes_info[36];
    char auth_tag[16];
    char data[0];
} uma_request_enc;


typedef struct uma_responce_enc
{
    unsigned int size;
    char gcm_iv[16];
    char auth_tag[16];
    char data[0];
} uma_responce_enc;


typedef struct uma_enc_info
{
    char secret[0x20];
    char session_id[0x10];
    char auth[0x10];
} uma_enc_info;


typedef struct rng_s
{
    uint64_t x1;
    uint64_t x2;
} rng_s;


int f_rng(void *p_rng, unsigned char *output, size_t output_len)
{
    for (; output_len; ++output) {
        --output_len;
        rng_s *rng = (rng_s *)p_rng;
        uint32_t tmp = (uint32_t)((rng->x1 ^ (rng->x1 >> 18)) >> 27);
        *output = (char)(rotr(tmp, (rng->x1 >> 59)) & 0xFF);
        rng->x1 = rng->x2 + 0x5851F42D4C957F2DLL * rng->x1;
    }
    return 0;
}


void compress_alg(char *d1, char *d2, char *d3, char *out)
{
    char c1, c2, c3, c4;
    memcpy(out, d2, 16);

    for (int i = 0; i < 16; ++i) {
        c1 = d1[i] ^ out[i];
        c2 = d2[c1 & 0xF] ^ d1[i];
        c3 = out[c2 & 0xF] ^ d1[i];
        c4 = d3[c3 & 0xF] ^ d1[i];
        out[c2 & 0xF] ^= c1;
        out[c3 & 0xF] ^= c2;
        out[c4 & 0xF] ^= c3;
        out[c1 & 0xF] ^= c4;
    }
}


void compress(char *src, size_t src_size, char *path)
{
    char dst[src_size+0x100];
    uma_request *req = (uma_request *)src;
    uma_request_enc *req_enc = (uma_request_enc *)&dst;

    mbedtls_ecdh_context ecdh;
    mbedtls_ctr_drbg_context ctr_drbg;

    uint64_t rng, p_rng;
    rng = (2 * bswap_64(*(uint64_t *)&req->random_bytes[8])) | 1;
    p_rng = rng + 0x5851F42D4C957F2DLL * (rng + bswap_64(*(uint64_t *)req->random_bytes));
    for (int i = 0; i < (req->session_id[0] & 0xF); ++i) {
        p_rng = rng + 0x5851F42D4C957F2DLL * p_rng;
    }

    //mbedtls_ctr_drbg_init(&ctr_drbg);  // will overflow
    memcpy(ctr_drbg.counter, (void *)&p_rng, sizeof(p_rng));
    memcpy(ctr_drbg.counter+8, (void *)&rng, sizeof(rng));

    mbedtls_ecdh_init(&ecdh);
    mbedtls_ecp_group_load( &ecdh.grp, MBEDTLS_ECP_DP_CURVE25519);
    mbedtls_ecdh_gen_public(&ecdh.grp, &ecdh.d, &ecdh.Q, f_rng, &ctr_drbg);

    memcpy(req_enc->client_pubkey, ecdh.Q.X.p, 0x20);

    mbedtls_mpi_lset(&ecdh.Qp.Z, 1);
    mbedtls_mpi_read_binary(&ecdh.Qp.X, req->server_pub_key, 0x20);
    mbedtls_ecdh_compute_shared(&ecdh.grp, &ecdh.z, &ecdh.Qp, &ecdh.d, f_rng, &ctr_drbg);

    char aes_plaintext[36];
    char aes_data[16];
    char aes_data2[16];
    char aes_key[16];
    char auth[16];
    unsigned int input_size = src_size - req->pre_size - 4;
    char *input;
    mbedtls_md5_context md5_ctx;
    if (req->pre_size < 0x78) {
        // no auth key
        memcpy(aes_plaintext, "\x00\x00", 2);
        memcpy(aes_plaintext+2, req->cert_uuid, 16);
        f_rng(&ctr_drbg, aes_plaintext+18, 18);
        memcpy(aes_data, req->cert_uuid, 16);
        memcpy(auth, req->cert_uuid, 16);
        input = req->auth_key;

    } else {
        memcpy(aes_plaintext, "\x01\x00", 2);
        memcpy(aes_plaintext+2, req->auth_key, 34);
        mbedtls_md5_init(&md5_ctx);
        mbedtls_md5_starts(&md5_ctx);
        mbedtls_md5_update(&md5_ctx, req->session_id, 0x10);
        mbedtls_md5_update(&md5_ctx, req->auth_key+34, 0x10);
        mbedtls_md5_update(&md5_ctx, req->cert_uuid, 0x10);
        mbedtls_md5_finish(&md5_ctx, aes_data);
        memcpy(auth, req->auth_key+34, 0x10);
        input = req->data;
    }
    compress_alg(aes_data, (char *)ecdh.z.p, req->auth_data, aes_data2);

    mbedtls_md5_init(&md5_ctx);
    mbedtls_md5_starts(&md5_ctx);
    mbedtls_md5_update(&md5_ctx, aes_data2, 0x10);
    mbedtls_md5_update(&md5_ctx, (char *)ecdh.z.p, 0x20);
    mbedtls_md5_update(&md5_ctx, aes_data, 0x10);
    mbedtls_md5_update(&md5_ctx, req->auth_data, 0x14);
    mbedtls_md5_finish(&md5_ctx, aes_key);

    mbedtls_aes_context aes_ctx;
    size_t nc_offset = 0;
    mbedtls_aes_init(&aes_ctx);
    mbedtls_aes_setkey_enc(&aes_ctx, (char *)ecdh.z.p, 256);
    mbedtls_aes_crypt_ctr(&aes_ctx, 0x24, &nc_offset, (char *)ecdh.Q.X.p, aes_data, aes_plaintext, req_enc->aes_info);
    mbedtls_aes_free(&aes_ctx);

    char gcm_iv[16];
    mbedtls_md5_init(&md5_ctx);
    mbedtls_md5_starts(&md5_ctx);
    mbedtls_md5_update(&md5_ctx, req_enc->client_pubkey, 0x20);
    mbedtls_md5_update(&md5_ctx, req->session_id, 0x10);
    mbedtls_md5_update(&md5_ctx, req->cert_uuid, 0x10);
    mbedtls_md5_finish(&md5_ctx, gcm_iv);
    mbedtls_md5_free(&md5_ctx);

    mbedtls_gcm_context gcm_ctx;
    mbedtls_gcm_init(&gcm_ctx);
    mbedtls_gcm_setkey(&gcm_ctx, MBEDTLS_CIPHER_ID_AES, aes_key, 128);
    mbedtls_gcm_starts(&gcm_ctx, MBEDTLS_GCM_ENCRYPT, gcm_iv, 0x10, req->auth_data, 0x34);
    mbedtls_gcm_update(&gcm_ctx, input_size, input, req_enc->data);
    mbedtls_gcm_finish(&gcm_ctx, req_enc->auth_tag, 0x10);
    mbedtls_gcm_free(&gcm_ctx);
    input_size += 0x54;
    req_enc->size = input_size;

    char tmp[0x100];
    snprintf(tmp, 0x100, "%s/req.enc", path);
    FILE *fp = fopen(tmp, "w");
    fwrite(&dst, 1, input_size+4, fp);
    fclose(fp);

    snprintf(tmp, 0x100, "%s/info", path);
    fp = fopen(tmp, "w");
    uma_enc_info enc_info;
    memcpy(enc_info.secret, ecdh.z.p, 0x20);
    memcpy(enc_info.session_id, req->session_id, 0x10);
    memcpy(enc_info.auth, auth, 0x10);
    fwrite((void *)&enc_info, 1, sizeof(enc_info), fp);
    fclose(fp);

    mbedtls_ecdh_free(&ecdh);
}


void decompress(char *src, size_t src_size, char *path)
{
    char tmp[0x100];
    size_t dst_size;
    uma_responce_enc *resp_enc = (uma_responce_enc *)src;
    if (resp_enc->size == 0) {
        dst_size = src_size - 0x24;
    } else {
        dst_size = resp_enc->size;
    }
    char dst[dst_size+0x100];
    uma_enc_info enc_info;

    snprintf(tmp, 0x100, "%s/info", path);
    FILE *fp = fopen(tmp, "r");
    fread((void *)&enc_info, 1, sizeof(enc_info), fp);
    fclose(fp);

    char aes_key[16];

    mbedtls_md5_context md5_ctx;
    mbedtls_md5_init(&md5_ctx);
    mbedtls_md5_starts(&md5_ctx);
    mbedtls_md5_update(&md5_ctx, enc_info.secret, 0x20);
    mbedtls_md5_update(&md5_ctx, enc_info.session_id, 0x10);
    mbedtls_md5_update(&md5_ctx, enc_info.auth, 0x10);
    mbedtls_md5_finish(&md5_ctx, aes_key);
    mbedtls_md5_free(&md5_ctx);

    mbedtls_gcm_context gcm_ctx;
    mbedtls_gcm_init(&gcm_ctx);
    mbedtls_gcm_setkey(&gcm_ctx, MBEDTLS_CIPHER_ID_AES, aes_key, 128);
    mbedtls_gcm_starts(&gcm_ctx, MBEDTLS_GCM_DECRYPT, resp_enc->gcm_iv, 0x10, enc_info.session_id, 0x20);
    mbedtls_gcm_update(&gcm_ctx, src_size-0x24, resp_enc->data, dst);
    mbedtls_gcm_finish(&gcm_ctx, resp_enc->auth_tag, 0x10);
    mbedtls_gcm_free(&gcm_ctx);

    char dst2[dst_size+0x100];
    if (resp_enc->size) {
        LZ4_decompress_safe(dst, dst2, dst_size, dst_size+0x100);
    }

    snprintf(tmp, 0x100, "%s/resp.dec", path);
    fp = fopen(tmp, "w");
    if (resp_enc->size)
        fwrite(dst2, 1, dst_size, fp);
    else
        fwrite(dst, 1, dst_size, fp);
    fclose(fp);
}


int main(int argc, char **argv)
{
    if (argc != 3) {
        printf("enc/dec path\n");
        return 0;
    }

    char input[0x3000];
    char tmp[0x100];
    FILE *fp;

    if (atoi(argv[1]) == 0) {
        //printf("Enc request...\n");
        snprintf(tmp, 0x100, "%s/req", argv[2]);
        fp = fopen(tmp, "r");
        size_t size = fread(input, 1, 0x3000, fp);
        compress(input, size, argv[2]);
    } else {
        //printf("Dec response...\n");
        snprintf(tmp, 0x100, "%s/resp", argv[2]);
        fp = fopen(tmp, "r");
        size_t size = fread(input, 1, 0x3000, fp);
        decompress(input, size, argv[2]);
    }
    fclose(fp);

    return 0;
}



