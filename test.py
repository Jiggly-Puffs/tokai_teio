# -*- coding: utf-8 -*-

import json
import derby
import pprint
import asyncio
import logging
from client import UmaClient
logger = logging.getLogger(__name__)


class UmaException(Exception):
    pass

class ShutdownHandler(logging.StreamHandler):
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            raise UmaException("Uma Error")


async def test_signup(num, name=None, sex=None):
    for i in range(num):
            logger.info("Breeding uma %d" % (i+1))
            client = UmaClient()
            await client.signup(name, sex)
            await client.run(derby.Gifts)
            info = await client.get_info()
            await asyncio.sleep(3)


async def test_single_mode(self, data):
    client = UmaClient(data)
    await client.signin()
    await client.run(derby.Training)

async def job():
    await test_signup(1)


async def main():
    jobs = []
    for i in range(1):
        jobs.append(job())
    await asyncio.gather(*jobs)



if __name__ == "__main__":
    # test
    import coloredlogs
    coloredlogs.install(logging.DEBUG)
    logging.getLogger().addHandler(ShutdownHandler())

    import dotenv
    dotenv.load_dotenv() # install .env into os.env

    asyncio.run(main())
