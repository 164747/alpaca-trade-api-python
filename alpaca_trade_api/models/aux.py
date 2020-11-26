from __future__ import annotations

import typing
import uuid
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field




class OrderTimeInFore(Enum):
    DAY = 'day'


class OrderType(Enum):
    LIMIT = 'limit'


class OrderClass(Enum):
    SIMPLE = 'simple'


class StopLoss(BaseModel):
    stop_price: float
    limit_price: float


class OrderBase(BaseModel):
    client_order_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    qty: int
    time_in_force: OrderTimeInFore = OrderTimeInFore.DAY
    limit_price: typing.Optional[Decimal]
    stop_price: typing.Optional[Decimal] = None
