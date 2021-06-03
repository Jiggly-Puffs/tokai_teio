import os
from tortoise import Tortoise

async def init():
    db_url = os.environ.get("DATABASE_URL")
    assert db_url is not None

    await Tortoise.init(
        db_url=db_url,
        modules={'model': ['model']}
    )
