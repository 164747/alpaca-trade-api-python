from __future__ import annotations

import typing
import uuid
from enum import Enum

from pydantic import BaseModel, Field

import alpaca_trade_api as tradeapi


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
        client: tradeapi.REST = None

    @property
    def client(self) -> tradeapi.REST:
        c = self.Meta.client is not None
        assert c is not None
        return c


class OrderBase(AplacaModel):
    client_order_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    qty: int
    time_in_force: OrderTimeInFore = OrderTimeInFore.DAY
    limit_price: typing.Optional[float]
    stop_price: typing.Optional[float] = None