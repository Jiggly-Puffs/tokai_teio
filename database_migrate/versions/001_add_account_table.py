from sqlalchemy import Table, MetaData, String, Column, BigInteger, DateTime, Unicode
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import UniqueConstraint, ForeignKey
import logging
logger = logging.getLogger(__name__)

meta = MetaData()

tables = []
indexs = []

account_table = Table(
    'account', meta,
    Column('id', BigInteger, primary_key=True),

    Column('viewer_id', BigInteger, unique=True),
    Column('create_timestamp', DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column('update_timestamp', DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()),
    Column('latest_login_timestamp', DateTime(timezone=True), server_default='1970-01-01', nullable=False),
    Column('latest_refresh_timestamp', DateTime(timezone=True), server_default='1970-01-01', nullable=False),

    Column('gender', String),
    Column('nickname', String),
    Column('fcoin', BigInteger),

    Column('auth_type', String, nullable=False),
    Column('auth_key', String),
    Column('app_viewer_id', String),
    Column('password', String),

    Column('firebase', JSONB),
    Column('device_info', JSONB),
    )
tables.append(account_table)

card_prototype_table = Table(
    'card_prototype', meta,

    # same as `card_id` in response
    Column('id', BigInteger, primary_key=True, autoincrement=False),
    Column('name', Unicode)
)
tables.append(card_prototype_table)

card_table = Table(
    'card', meta,

    Column('id', BigInteger, primary_key=True),

    # which account this card belongs to
    Column('account_id', BigInteger, ForeignKey(account_table.c.id, ondelete='CASCADE'), nullable=False),
    # card prototype_id (i.e `card_id` in response)
    Column('prototype_id', BigInteger, ForeignKey(card_prototype_table.c.id, ondelete='SET NULL')),
    Column('rarity', BigInteger),
    Column('talent_level', BigInteger),

    UniqueConstraint('account_id', 'prototype_id')
)
tables.append(card_table)

support_card_prototype_table = Table(
    'support_card_prototype', meta,

    # same as `card_id` in response
    Column('id', BigInteger, primary_key=True, autoincrement=False),
    Column('name', Unicode)
)
tables.append(support_card_prototype_table)

support_card_table = Table(
    'support_card', meta,

    Column('id', BigInteger, primary_key=True),

    # which account this card belongs to
    Column('account_id', BigInteger, ForeignKey(account_table.c.id, ondelete='CASCADE'), nullable=False),
    Column('prototype_id', BigInteger, ForeignKey(support_card_prototype_table.c.id, ondelete='SET NULL')),
    Column('favorite_flag', BigInteger, nullable=False),
    Column('limit_break_count', BigInteger, nullable=False),
    Column('stock', BigInteger, nullable=False),
    Column('exp', BigInteger, nullable=False),

    UniqueConstraint('account_id', 'prototype_id')
)
tables.append(support_card_table)




def upgrade(migrate_engine):

    meta.bind = migrate_engine

    for table in tables:
        logging.info("creating table %s", table.name)
        table.create()
        logging.info("table %s created", table.name)


def downgrade(migrate_engine):

    meta.bind = migrate_engine

    for table in tables[::-1]:
        logging.info("dropping table %s", table.name)
        table.drop()
        logging.info("table %s droppped", table.name)
