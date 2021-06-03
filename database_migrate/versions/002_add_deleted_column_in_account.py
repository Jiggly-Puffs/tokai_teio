from sqlalchemy import Table, MetaData, Column, Boolean
import logging
logger = logging.getLogger("__name__")

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    account = Table('account', meta, autoload=True)
    is_deleted_column = Column('is_deleted', Boolean, nullable=False, server_default='f')
    is_deleted_column.create(account)

    logger.info("`is_deleted' column created in table `account'")


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    raise Exception("not allow to downgrade")
