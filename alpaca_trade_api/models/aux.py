from __future__ import annotations

import datetime
import pytz
import typing
import uuid
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, PrivateAttr

import alpaca_trade_api as tradeapi
from alpaca_trade_api.common import URL


class OrderTimeInFore(Enum):
    DAY = 'day'


class OrderType(Enum):
    LIMIT = 'limit'


class OrderClass(Enum):
    SIMPLE = 'simple'


class StopLoss(BaseModel):
    stop_price: float
    limit_price: float


class AplacaModel(BaseModel):
    class Meta:
        trade_client: tradeapi.REST = None
        data_client: tradeapi.REST = None

    @property
    def client(self) -> tradeapi.REST:
        c = self.Meta.trade_client is not None
        assert c is not None
        return c

    @classmethod
    def register(cls, key_id : str, secret_key : str, trade_url : URL, data_url : URL):
        cls.Meta.trade_client = tradeapi.REST(key_id=key_id, secret_key=secret_key, base_url=trade_url)
        cls.Meta.data_client = tradeapi.REST(key_id=key_id, secret_key=secret_key, base_url=data_url)


class OrderBase(AplacaModel):
    client_order_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    qty: int
    time_in_force: OrderTimeInFore = OrderTimeInFore.DAY
    limit_price: typing.Union[float, Decimal, None] = None
    stop_price: typing.Union[float, Decimal, None] = None

    _created_at: datetime.datetime = PrivateAttr(default_factory=lambda: datetime.datetime.now(tz=pytz.UTC))

    def __str__(self):
        return f'[{self.qty}] @ {self.limit_price} {self.age}'


    @property
    def age(self) -> datetime.timedelta:
        return datetime.datetime.now(tz=pytz.UTC) - self._created_at
