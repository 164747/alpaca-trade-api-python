from __future__ import annotations

import datetime
import json
import typing
from decimal import Decimal
from enum import Enum

import pytz
from pydantic import Field, PrivateAttr

from alpaca_trade_api.models import aux
from alpaca_trade_api.rest import APIError


class OrderSide(Enum):
    BUY = 'buy'
    SELL = 'sell'


class OrderReplace(aux.OrderBase):
    trail: typing.Optional[float] = None


class OrderPlace(aux.OrderBase):
    symbol: str
    qty: int
    order_type: str = Field(alias='type', default=aux.OrderType.LIMIT)
    side: OrderSide
    time_in_force: aux.OrderTimeInFore = aux.OrderTimeInFore.DAY
    extended_hours: bool = False
    trail_price: typing.Union[float, Decimal, None] = None
    trail_percent: typing.Union[float, Decimal, None] = None
    order_class: aux.OrderClass = aux.OrderClass.SIMPLE
    stop_loss: typing.Optional[aux.StopLoss] = None


class Order(OrderPlace):
    order_id: str = Field(alias='id')
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
    hwm: typing.Optional[float] = None
    _pending_delete: bool = PrivateAttr(default=False)
    _pending_replace: bool = PrivateAttr(default=False)
    _change_request: typing.Optional[OrderReplace] = PrivateAttr(default=None)
    _delete_req_at: typing.Optional[datetime.datetime] = PrivateAttr(default=None)

    @property
    def unmatched_qty(self) -> int:
        return self.qty - self.filled_qty

    @classmethod
    def place_order(cls: Order, order_place: OrderPlace):
        data = json.loads(order_place.json(exclude_none=True, by_alias=True))
        cls.Meta.client.post('/orders', data=data)

    def update_order(self, order_replace: OrderReplace):
        data = json.loads(order_replace.json(exclude_none=True, by_alias=True))
        try:
            self.Meta.client.patch(f'/orders/{self.order_id}', data=data)
            self._change_request = order_replace
            self._pending_replace = True
        except APIError as e:
            if e.status_code != 422:
                raise

    def delete(self):
        self.Meta.client.delete(f'/orders/{self.order_id}')
        self._pending_delete = True
        self._delete_req_at = datetime.datetime.now(tz=pytz.UTC)

    @staticmethod
    def delete_all():
        Order.Meta.client.delete(f'/orders')

    @property
    def pending_action(self) -> bool:
        return self._pending_delete or self._pending_replace

    @property
    def pending_age(self) -> datetime.timedelta:
        if self._pending_replace:
            return self._change_request.age
        if self._pending_delete:
            return datetime.datetime.now(tz=pytz.UTC) - self._delete_req_at
        return datetime.timedelta(0)

    @classmethod
    def get(cls: Order, status: str = None,
            limit: int = None,
            after: str = None,
            until: str = None,
            direction: str = None,
            params=None,
            nested: bool = None) -> typing.List[Order]:
        params = locals()
        params.pop('cls')
        return [Order(**x) for x in Order.Meta.client.get('/orders', params)]


Order.update_forward_refs()


class Account(aux.AplacaModel):
    account_blocked: bool
    account_number: str
    buying_power: float
    cash: float
    created_at: datetime.datetime
    currency: str
    daytrade_count: int
    daytrading_buying_power: float
    equity: float
    id: str
    initial_margin: float
    last_equity: float
    last_maintenance_margin: float
    long_market_value: float
    maintenance_margin: float
    multiplier: float
    pattern_day_trader: bool
    portfolio_value: float
    regt_buying_power: float
    short_market_value: float
    shorting_enabled: bool
    sma: float
    status: str
    trade_suspended_by_user: bool
    trading_blocked: bool
    transfers_blocked: bool

    @classmethod
    def get(cls: Account) -> Account:
        return Account(**Account.Meta.client.get('/account'))


class Position(aux.AplacaModel):
    asset_id: str
    symbol: str
    exchange: str
    asset_class: str
    avg_entry_price: float
    qty: int
    side: str
    market_value: float
    cost_basis: float
    unrealized_pl: float
    unrealized_plpc: float
    unrealized_intraday_pl: float
    unrealized_intraday_plpc: float
    current_price: float
    lastday_price: float
    change_today: float

    @classmethod
    def get(cls: Position) -> typing.List[Position]:
        return [Position(**x) for x in cls.Meta.client.get('/positions')]

    @property
    def net_position(self) -> int:
        return self.qty


class Activity(aux.AplacaModel):
    activity_type: str
    id: str

    @classmethod
    def get(cls: Activity, date: str = None, until: str = None, after: str = None, direction: str = 'desc',
            page_size: int = 100, page_token: str = None) -> typing.List[typing.Union[TradeActivity, NonTradeActivity]]:
        d = locals()
        d.pop('cls')
        dl = Activity.Meta.client.get('/account/activities', d)
        return [TradeActivity(**d) if d['activity_type'] == 'FILL' else NonTradeActivity(**d) for d in dl]

    @property
    def is_trade(self) -> bool:
        return isinstance(self, TradeActivity)


class TradeActivity(Activity):
    cum_qty: int
    leaves_qty: int
    price: float
    qty: int
    side: OrderSide
    symbol: str
    transaction_time: datetime.datetime
    order_id: str
    type: str


class NonTradeActivity(Activity):
    date: datetime.date
    net_amount: float
    symbol: typing.Optional[str] = None
    qty: typing.Optional[int] = None
    per_share_amount: typing.Optional[float] = None


class MarketClock(aux.AplacaModel):
    timestamp: datetime.datetime
    is_open: bool
    next_open: datetime.datetime
    next_close: datetime.datetime

    @classmethod
    def get(cls: MarketClock) -> MarketClock:
        return MarketClock(**cls.Meta.client.get('/clock'))

    @property
    def opens_in(self) -> datetime.timedelta:
        return self.next_open - datetime.datetime.now(tz=pytz.UTC)

    @property
    def closes_in(self) -> datetime.timedelta:
        return self.next_close - datetime.datetime.now(tz=pytz.UTC)

    @property
    def age(self) -> datetime.timedelta:
        return datetime.datetime.now(tz=pytz.UTC) - self.timestamp


def __main():
    d = {'id': '5b8198c9-67a0-43a3-a646-9f16989071f8', 'client_order_id': '591c6ddf-44ce-4183-997e-9f00f0118885',
         'created_at': '2020-11-30T18:52:40.673236Z', 'updated_at': '2020-11-30T18:52:40.673236Z',
         'submitted_at': '2020-11-30T18:52:40.667742Z', 'filled_at': None, 'expired_at': None, 'canceled_at': None,
         'failed_at': None, 'replaced_at': None, 'replaced_by': None, 'replaces': None,
         'asset_id': 'f30d734c-2806-4d0d-b145-f9fade61432b', 'symbol': 'GOOG', 'asset_class': 'us_equity', 'qty': '1',
         'filled_qty': '0', 'filled_avg_price': None, 'order_class': 'simple', 'order_type': 'limit', 'type': 'limit',
         'side': 'sell', 'time_in_force': 'day', 'limit_price': '1762.6', 'stop_price': None, 'status': 'accepted',
         'extended_hours': False, 'legs': None, 'trail_percent': None, 'trail_price': None, 'hwm': None}
    order = Order(**d)
    print(order)


if __name__ == '__main__':
    __main()
