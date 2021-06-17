import logging
import asyncio
import model
import argparse
import db
import datetime
import derby
from client import UmaClient

logger = logging.getLogger(__name__)

g_sem: asyncio.Semaphore

async def job(account: model.Account):
    data = {}
    data["device_info"] = account.device_info
    data["auth_key"] = account.auth_key
    data["viewer_id"] = account.viewer_id
    data["firebase"] = account.firebase
    data["app_viewer_id"] = account.app_viewer_id

    client = UmaClient(data)
    await client.signin()

    # recieve all gifts
    await derby.Gifts(client).run()

    info = await client.get_info()

    logger.info("update support_card & card %d", account.id)
    for support_card_j in info["support_card_list"]:
        support_card_prototype, _ = await model.SupportCardPrototype.get_or_create(
            id = support_card_j["support_card_id"],
        )
        support_card, _ = await model.SupportCard.get_or_create(
            account_id = account.id,
            prototype_id = support_card_prototype.id,
        )
        support_card.favorite_flag = support_card_j["favorite_flag"]
        support_card.limit_break_count = support_card_j["limit_break_count"]
        support_card.stock = support_card_j["stock"]
        support_card.exp = support_card_j["exp"]
        await support_card.save()

    for card_j in info["card_list"]:
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
    logger.info("update support_card & card done %d", account.id)

    account.latest_refresh_timestamp = datetime.datetime.now()
    account.fcoin = info["fcoin"]
    await account.save()

async def main():

    parser = argparse.ArgumentParser()
    options = parser.parse_args()

    await db.init()

    accounts = model.Account.all().filter(is_deleted=False).order_by('latest_refresh_timestamp')
    no_concurrent = 250
    dltasks = set()
    loop = asyncio.get_event_loop()
    async for account in accounts:
        if len(dltasks) >= no_concurrent:
            _done, dltasks = await asyncio.wait(
                dltasks, return_when=asyncio.FIRST_COMPLETED)
        dltasks.add(loop.create_task(job(account)))
    await asyncio.wait(dltasks)


if __name__ == "__main__":
    import coloredlogs
    coloredlogs.install(logging.INFO)

    import dotenv
    dotenv.load_dotenv() # install .env into os.env

    asyncio.run(main())

