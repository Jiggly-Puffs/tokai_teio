.PHONY: clean all

proto=./proto 

all: proto

$(proto): proto.c
	gcc $< -o $(proto) -lmbedtls -lmbedcrypto -llz4 -L/usr/local/lib -I/usr/local/include/mbedtls -static 

clean:
	rm -rf proto
