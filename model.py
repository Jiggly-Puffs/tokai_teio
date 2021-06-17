from tortoise.models import Model
from tortoise import fields
from typing import Optional
import datetime
import enum

__all__ = (
    "Gender",
    "AuthType",
    "Account",
    "CardPrototype",
    "Card",
    "SupportCardPrototype",
    "SupportCard",
)


class Gender(enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class AuthType(enum.Enum):
    APP_VIEWER_ID = "app_viewer_id"
    PASSWORD = "password"


class Account(Model):
    class Meta:
        table = 'account'

    id: int = fields.BigIntField(pk=True, source_field='id', null=False)

    create_timestamp: datetime.datetime = fields.DatetimeField(null=False, auto_now_add=True)
    update_timestamp: datetime.datetime = fields.DatetimeField(null=False, auto_now=True)
    latest_login_timestamp: datetime.datetime = fields.DatetimeField(null=False, default=datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc))
    latest_refresh_timestamp: datetime.datetime = fields.DatetimeField(null=False, default=datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc))

    is_deleted: bool = fields.BooleanField(null=False, default=False) # type: ignore

    viewer_id: int = fields.BigIntField(unique=True)

    gender: Optional[Gender] = fields.CharEnumField(Gender, max_length=64, null=True)
    nickname: Optional[str] = fields.TextField()
    fcoin: int = fields.BigIntField()

    auth_type: AuthType = fields.CharEnumField(AuthType, max_length=64)
    auth_key: Optional[str] = fields.TextField()
    app_viewer_id: Optional[str] = fields.TextField()
    password: Optional[str] = fields.TextField()

    device_info = fields.JSONField()
    firebase = fields.JSONField()

    cards: fields.ReverseRelation['Card']
    support_cards: fields.ReverseRelation['SupportCard']



class CardPrototype(Model):
    class Meta:
        table = 'card_prototype'

    # same as `card_id` in response

    # NOTE: this field should not be autoincrement, but orm model does not supported to define it
    id = fields.BigIntField(pk=True, null=False)
    name = fields.TextField()

    cards: fields.ReverseRelation['Card']

class Card(Model):
    class Meta:
        table = 'card'

    id: int = fields.BigIntField(pk=True, null=False)

    account: fields.ForeignKeyNullableRelation[Account] = \
            fields.ForeignKeyField("model.Account", source_field='account_id', related_name="cards") # type: ignore
    prototype: fields.ForeignKeyNullableRelation[CardPrototype] = \
            fields.ForeignKeyField("model.CardPrototype", source_field='prototype_id', related_name="cards") # type: ignore

    rarity = fields.BigIntField()
    talent_level = fields.BigIntField()


class SupportCardPrototype(Model):
    class Meta:
        table = 'support_card_prototype'

    id = fields.BigIntField(pk=True, null=False)
    name = fields.TextField()

    support_cards: fields.ReverseRelation['SupportCard']

class SupportCard(Model):
    class Meta:
        table = 'support_card'
    id: int = fields.BigIntField(pk=True, null=False)

    account: fields.ForeignKeyNullableRelation[Account] = \
            fields.ForeignKeyField("model.Account", source_field='account_id', related_name="support_cards") # type: ignore
    prototype: fields.ForeignKeyNullableRelation[SupportCardPrototype] = \
            fields.ForeignKeyField("model.SupportCardPrototype", source_field='prototype_id', related_name="support_cards") # type: ignore

    favorite_flag = fields.BigIntField()
    limit_break_count = fields.BigIntField()
    stock = fields.BigIntField()
    exp = fields.BigIntField()
