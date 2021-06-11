from sqlalchemy import Table, MetaData, Column, Boolean
import logging
logger = logging.getLogger("__name__")

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    support_card_table = Table('support_card', meta, autoload=True)
    support_card_table.c.favorite_flag.alter(nullable=True)
    support_card_table.c.limit_break_count.alter(nullable=True)
    support_card_table.c.stock.alter(nullable=True)
    support_card_table.c.exp.alter(nullable=True)

    logger.info("done")


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    raise Exception("not allow to downgrade")
