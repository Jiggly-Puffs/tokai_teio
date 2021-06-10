import logging
import aiofiles
import asyncio
import json
import model
import argparse
import db
from client import UmaClient

logger = logging.getLogger(__name__)

sem: asyncio.Semaphore

async def job(account: model.Account):
    async with sem:
        data = {}
        data["device_info"] = account.device_info
        data["auth_key"] = account.auth_key
        data["viewer_id"] = account.viewer_id
        data["firebase"] = account.firebase
        data["app_viewer_id"] = account.app_viewer_id
        print(data)

        client = UmaClient(data)
        await client.signin()

        info = await client.get_info()
        for card_j in info["card_list"]:
            print("!!!", card_j["card_id"])
            card_prototype, _ = await model.CardPrototype.get_or_create(
                id = card_j["card_id"],
            )
            card, _ = await model.Card.get_or_create(
                account_id = account.id,
                prototype_id = card_prototype.id,
            )
            card.rarity = card_j["rarity"]
            card.talent_level = card_j["talent_level"]
            await card.save()

        for support_card_j in info["support_card_list"]:
            print("zzz", support_card_j["support_card_id"])
            print(support_card_j)
            support_card_prototype, _ = await model.CardPrototype.get_or_create(
                id = support_card_j["support_card_id"]
            )
            support_card, _ = await model.SupportCard.get_or_create(
                account = account,
                prototype = support_card_prototype,
            )
            support_card.favorite_flag = support_card_j["favorite_flag"]
            support_card.limit_break_count = support_card_j["limit_break_count"]
            support_card.stock = support_card_j["stock"]
            support_card.exp = support_card_j["exp"]
            await support_card.save()

        
        print(info["card_list"])
        print(info["support_card_list"])
        #card_id_list = info["card_list"]
        #support_card_id_list = info["support_card_list"]

        



async def main():
    global sem

    sem = asyncio.Semaphore(1)

    parser = argparse.ArgumentParser()
    options = parser.parse_args()

    await db.init()

    accounts = await model.Account.all().filter(is_deleted=False)
    jobs = []
    for account in accounts:
        jobs.append(job(account))
        
    await asyncio.gather(*jobs)


if __name__ == "__main__":
    import coloredlogs
    coloredlogs.install(logging.INFO)

    import dotenv
    dotenv.load_dotenv() # install .env into os.env

    asyncio.run(main())

