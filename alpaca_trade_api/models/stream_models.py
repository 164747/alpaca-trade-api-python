from __future__ import annotations

import datetime
import typing
from enum import Enum

from pydantic import BaseModel, Field

from alpaca_trade_api.models.rest_models import Order




class OrderEvent(Enum):
    NEW = 'new', False, True, False
    PENDING_NEW = 'pending_new', True, False, False
    PENDING_CANCEL = 'pending_cancel', True, False, False
    PENDING_REPLACE = 'pending_replace', True, False, False
    PARTIAL_FILL = 'partial_fill', False, True, False
    DONE_FOR_DAY = 'done_for_day', False, False, False
    REPLACE_REJECTED = 'order_replace_rejected', False, False, True
    CANCEL_REJECTED = 'order_cancel_rejected', False, False, True
    FILL = 'fill', False, False, False
    CANCELED = 'canceled', False, False, False
    EXPIRED = 'expired', False, False, False
    REPLACED = 'replaced', False, False, False
    REJECTED = 'rejected', False, False, True
    STOPPED = 'stopped', False, False, False
    CALCULATED = 'calculated', False, False, False
    SUSPENDED = 'suspended', False, False, False

    def __new__(cls, *args, **kwds):
        value = args[0]
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, text: str, is_pending: bool, is_active: bool, is_rejected : bool):
        self.text = text
        self.is_pending = is_pending
        self.is_active = is_active
        self.is_rejected = is_rejected

    @property
    def fill_event(self) -> bool:
        return self in {OrderEvent.FILL, OrderEvent.PARTIAL_FILL}

    @property
    def is_new(self) -> bool:
        return self is OrderEvent.NEW


class TradeBase(BaseModel):
    event: OrderEvent
    price: typing.Optional[float] = None
    utc: typing.Optional[datetime.datetime] = Field(alias='timestamp', default=None)
    position_qty: typing.Optional[int] = None
    order: Order

    @property
    def has_qty(self) -> bool:
        return self.position_qty is not None


def __main():
    oe = OrderEvent('fill')
    print(oe)
    print(oe.value)
    print(oe.text)
    print(oe.is_pending)


if __name__ == '__main__':
    __main()
