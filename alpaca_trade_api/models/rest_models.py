from __future__ import annotations

import datetime
import typing
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field

from alpaca_trade_api.models import aux

# _T = typing.TypeVar('_T')
_T = typing.ClassVar

class OrderSide(Enum):
    BUY = 'buy'
    SELL = 'sell'



class OrderReplace(aux.OrderBase):
    trail: typing.Optional[Decimal] = None


class OrderPlace(aux.OrderBase):
    symbol: str
    qty: int
    order_type: str = Field(alias='type', default=aux.OrderType.LIMIT)
    side: OrderSide
    time_in_force: aux.OrderTimeInFore = aux.OrderTimeInFore.DAY
    limit_price: typing.Optional[Decimal] = None
    stop_price: typing.Optional[Decimal] = None
    extended_hours: bool = False
    trail_price: typing.Optional[Decimal] = None
    trail_percent: typing.Optional[Decimal] = None
    order_class: aux.OrderClass = aux.OrderClass.SIMPLE
    stop_loss: typing.Optional[aux.StopLoss] = None


class Order(OrderPlace):
    order_id: str
    created_at: datetime.datetime
    submitted_at: typing.Optional[datetime.datetime] = None
    filled_at: typing.Optional[datetime.datetime] = None
    expired_at: typing.Optional[datetime.datetime] = None
    cancelled_at: typing.Optional[datetime.datetime] = None
    failed_at: typing.Optional[datetime.datetime] = None
    replaced_at: typing.Optional[datetime.datetime] = None
    replaced_by: typing.Optional[str] = None
    replaces: typing.Optional[str] = None
    asset_id: str
    asset_class: str
    filled_qty: int
    status: str
    legs: typing.Optional[typing.List[Order]] = None
    hwm: Decimal


