import os
from tortoise import Tortoise
import logging

__all__ = (
    "init",
)

logger = logging.getLogger(__name__)

async def init():
    db_url = os.environ.get("DATABASE_URL")
    logger.info("use database url: %s", db_url)
    assert db_url is not None

    await Tortoise.init(
        db_url=db_url,
        modules={'model': ['model']}
    )
