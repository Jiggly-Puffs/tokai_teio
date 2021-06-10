import logging
import aiofiles
import asyncio
import json
import model
import argparse
import db

logger = logging.getLogger(__name__)

sem: asyncio.Semaphore

async def job(j):
    async with sem:

        device_info = j["device_info"]
        viewer_id = device_info["viewer_id"]
        app_viewer_id = j["app_viewer_id"]
        auth_key = j["auth_key"]

        account = model.Account(
                app_viewer_id = app_viewer_id,
                viewer_id = viewer_id,
                auth_key = auth_key,
                device_info = device_info,
                auth_type = "app_viewer_id",
                )
        await account.save()
        logger.info("commited viewer_id: %d" % account.viewer_id)


async def main():
    global sem

    sem = asyncio.Semaphore(100)

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", dest="input", required=True, type=str)

    options = parser.parse_args()

    await db.init()

    async with aiofiles.open(options.input, "r") as f:
        ids = await model.Account.all().values_list("viewer_id", flat=True)
        ids = set(ids)
        
        jobs = []
        while True:
            line = await f.readline()
            if line == "":
                break
            j = json.loads(line)

            device_info = j["device_info"]
            viewer_id = device_info["viewer_id"]
            if viewer_id in ids:
                logger.warning("viewer_id: %d is duplicated", viewer_id)
                continue

            jobs.append(job(j))

        await asyncio.gather(*jobs)


if __name__ == "__main__":
    import coloredlogs
    coloredlogs.install(logging.INFO)

    import dotenv
    dotenv.load_dotenv() # install .env into os.env

    asyncio.run(main())

