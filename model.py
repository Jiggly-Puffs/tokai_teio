from tortoise.models import Model
from tortoise import fields
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
        db_table = 'account'

    id = fields.BigIntField(pk=True, source_field='id', null=False)

    create_timestamp = fields.DatetimeField(null=False, auto_now_add=True)
    update_timestamp = fields.DatetimeField(null=False, auto_now=True)
    latest_login_timestamp = fields.DatetimeField(null=False, default=datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc))
    latest_refresh_timestamp = fields.DatetimeField(null=False, default=datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc))

    is_deleted = fields.BooleanField(null=False, default=False)

    viewer_id = fields.BigIntField(unique=True)

    gender = fields.CharEnumField(Gender, max_length=64, null=True)
    nickname = fields.TextField()
    fcoin = fields.TextField()

    auth_type = fields.CharEnumField(AuthType, max_length=64)
    auth_key = fields.TextField()
    app_viewer_id = fields.TextField()
    password = fields.TextField()

    device_info = fields.JSONField()
    firebase = fields.JSONField()

    cards: fields.ReverseRelation['Card']
    support_cards: fields.ReverseRelation['SupportCard']



class CardPrototype(Model):
    class Meta:
        db_table = 'card_prototype'

    # same as `card_id` in response

    # NOTE: this field should not be autoincrement, but orm model does not supported to define it
    id = fields.BigIntField(pk=True, null=False)
    name = fields.TextField()

    cards: fields.ReverseRelation['Card']

class Card(Model):
    __tablename__ = 'card'

    id: int = fields.BigIntField(pk=True, null=False)

    account: fields.ForeignKeyNullableRelation[Account] = \
            fields.ForeignKeyField("model.Account", source_field='account_id', related_name="cards") # type: ignore
    prototype: fields.ForeignKeyNullableRelation[CardPrototype] = \
            fields.ForeignKeyField("model.CardPrototype", source_field='prototype_id', related_name="cards") # type: ignore

    rarity = fields.BigIntField()
    talent_level = fields.BigIntField()


class SupportCardPrototype(Model):
    class Meta:
        db_table = 'support_card_prototype'

    id = fields.BigIntField(pk=True, null=False)
    name = fields.TextField()

    support_cards: fields.ReverseRelation['SupportCard']

class SupportCard(Model):
    class Meta:
        db_table = 'support_card'
    id: int = fields.BigIntField(pk=True, null=False)

    account: fields.ForeignKeyNullableRelation[Account] = \
            fields.ForeignKeyField("model.Account", source_field='account_id', related_name="support_cards") # type: ignore
    prototype: fields.ForeignKeyNullableRelation[SupportCardPrototype] = \
            fields.ForeignKeyField("model.SupportCardPrototype", source_field='prototype_id', related_name="support_cards") # type: ignore

    favorite_flag = fields.BigIntField(null=False)
    limit_break_count = fields.BigIntField(null=False)
    stock = fields.BigIntField(null=False)
    exp = fields.BigIntField(null=False)
