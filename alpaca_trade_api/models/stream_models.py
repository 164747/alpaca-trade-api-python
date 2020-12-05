from __future__ import annotations

import datetime
import typing
from enum import Enum

from pydantic import BaseModel, Field

from alpaca_trade_api.models.rest_models import Order


class OrderEventBase(Enum):

    # @property
    # def is_active(self) -> bool:
    #    raise NotImplementedError

    # @property
    # def is_pending(self) -> bool:
    #    return False

    # @property
    # def fill_event(self) -> bool:
    #   return False

    @property
    def is_new(self) -> bool:
        return False

    @property
    def is_rejected(self) -> bool:
        return False


class OrderEventPending(OrderEventBase):
    PENDING_NEW = 'pending_new'
    PENDING_CANCEL = 'pending_cancel'
    PENDING_REPLACE = 'pending_replace'


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


class OrderEvent(OrderEventBase):
    NEW = 'new', False, True
    PENDING_NEW = 'pending_new', True, False
    PENDING_CANCEL = 'pending_cancel', True, False
    PENDING_REPLACE = 'pending_replace', True, False
    PARTIAL_FILL = 'partial_fill', False, True
    DONE_FOR_DAY = 'done_for_day', False, False
    REPLACE_REJECTED = 'order_replace_rejected', False, False
    CANCEL_REJECTED = 'order_cancel_rejected', False, False
    FILL = 'fill', False, False
    CANCELED = 'canceled', False, False
    EXPIRED = 'expired', False, False
    REPLACED = 'replaced', False, False
    REJECTED = 'rejected', False, False
    STOPPED = 'stopped', False, False
    CALCULATED = 'calculated', False, False
    SUSPENDED = 'suspended', False, False

    def __new__(cls, *args, **kwds):
        value = args[0]
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, text: str, is_pending: bool, is_active: bool):
        self.text = text
        self.is_pending = is_pending
        self.is_active = is_active

    @property
    def fill_event(self) -> bool:
        return self in {OrderEvent.FILL, OrderEvent.PARTIAL_FILL}

    @property
    def is_new(self) -> bool:
        return self is OrderEvent.NEW


class TradeBase(BaseModel):
    event: typing.Union[OrderEventActive, OrderEventInActive]
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
