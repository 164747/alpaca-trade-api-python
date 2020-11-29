from __future__ import annotations

import datetime
import typing
from enum import Enum

from pydantic import BaseModel, Field

from alpaca_trade_api.models.rest_models import Order


class OrderEventBase(Enum):

    @property
    def is_active(self) -> bool:
        raise NotImplementedError


class OrderEventActive(OrderEventBase):
    NEW = 'new'
    PARTIAL_FILL = 'partial_fill'
    DONE_FOR_DAY = 'done_for_day'
    PENDING_NEW = 'pending_new'
    REPLACE_REJECTED = 'order_replace_rejected'
    CANCEL_REJECTED = 'order_cancel_rejected'
    PENDING_CANCEL = 'pending_cancel'
    PENDING_REPLACE = 'pending_replace'

    @property
    def is_active(self) -> bool:
        return True

    @property
    def fill_event(self) -> bool:
        return self is self.PARTIAL_FILL

    @property
    def is_new(self) -> bool:
        return False



class OrderEventInActive(OrderEventBase):
    FILL = 'fill'
    CANCELED = 'canceled'
    EXPIRED = 'expired'
    REPLACED = 'replaced'
    REJECTED = 'rejected'
    STOPPED = 'stopped'
    CALCULATED = 'calculated'
    SUSPENDED = 'suspended'

    @property
    def is_active(self) -> bool:
        return False

    @property
    def is_new(self) -> bool:
        return False

    @property
    def fill_event(self) -> bool:
        return self is self.FILL


class TradeBase(BaseModel):
    event: typing.Union[OrderEventActive, OrderEventInActive]
    price: typing.Optional[float] = None
    utc: typing.Optional[datetime.datetime] = Field(alias='timestamp', default=None)
    position_qty: typing.Optional[int] = None
    order: Order

    @property
    def has_qty(self) -> bool:
        return self.position_qty is not None
