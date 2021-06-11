import logging
import asyncio
import model
import db
from client import UmaClient, UmaClientResponseErrorException

logger = logging.getLogger(__name__)

sem: asyncio.Semaphore

async def job():
    while True:
        await asyncio.sleep(0.1)
        client = UmaClient()
        try:
            await client.signup()
        except UmaClientResponseErrorException as e:
            #FIXME: should have more specific Exception
            logger.warning("UserName duplicate?", exc_info=e, stack_info=True)
            continue
        except Exception as e:
            logger.error("Unknown Exception", exc_info=e)
            continue


        j = client.tojson()
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
    await db.init()
    jobs = []
    for _ in range(40):
        jobs.append(job())
    await asyncio.gather(*jobs)


if __name__ == "__main__":
    import coloredlogs
    coloredlogs.install(logging.INFO)

    import dotenv
    dotenv.load_dotenv() # install .env into os.env



    asyncio.run(main())

