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
        await derby.Gifts(client).run()
        info = await client.get_info()
        await asyncio.sleep(3)


async def test_single_mode():
    data = json.loads(open("./data/derby.json", "r").readlines()[-1])
    client = UmaClient(data)
    await client.signin()
    await derby.Gacha(client).run(5, [10, 1, 2, 1])
    await derby.SupportCard(client).run()
    await derby.Training(client).run()
    await derby.Gifts(client).run()
    info = await client.get_info()
    await test_team_race()


async def test_team_race():
    data = json.loads(open("./data/derby.json", "r").readlines()[-1])
    client = UmaClient(data)
    await client.signin()
    await derby.TeamRace(client).run(edit=True)
    info = await client.get_info()

async def test_gacha():
    data = json.loads(open("./data/derby.json", "r").readlines()[-1])
    client = UmaClient(data)
    await client.signin()
    await derby.Gacha(client).run(5, [1, 1, 1, 1])

async def job():
    await test_gacha()


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
