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
from sentry_sdk import capture_exception

class OrderSide(Enum):
    BUY = 'buy'
    SELL = 'sell'

    @property
    def is_sell(self) -> bool:
        return self is OrderSide.SELL

    @property
    def is_buy(self) -> bool:
        return self is OrderSide.BUY

    @property
    def other(self) -> OrderSide:
        if self.is_buy:
            return OrderSide.SELL
        else:
            return OrderSide.BUY
    @property
    def sign(self) -> float:
        if self.is_buy:
            return 1.0
        else:
            return -1.0

class ExtendedOrderSide(Enum):
    BUY = 'buy'
    SELL = 'sell'
    SHORT_SELL = 'sell_short'


    @property
    def is_sell(self) -> bool:
        return self is self.SELL or self is self.SHORT_SELL

    @property
    def is_buy(self) -> bool:
        return self is self.BUY

    @property
    def sign(self) -> float:
        if self.is_buy:
            return 1.0
        else:
            return -1.0




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

    def __str__(self):
        return f'{self.symbol} {self.side.value} [{self.qty}]@ {self.limit_price} {self.age}'


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
    _pending_place: bool = PrivateAttr(default=False)
    _replacing_order: typing.Optional[Order] = PrivateAttr(default=None)
    _change_request: typing.Optional[OrderReplace] = PrivateAttr(default=None)
    _delete_req_at: typing.Optional[datetime.datetime] = PrivateAttr(default=None)

    def __str__(self):
        return f'{self.symbol} {self.side.value} [{self.qty}]@ {self.limit_price} {self.age} {self.order_id} -> {self._change_request}'

    @property
    def unmatched_qty(self) -> int:
        return self.qty - self.filled_qty

    @classmethod
    async def place_order(cls: Order, order_place: OrderPlace) -> Order:
        data = json.loads(order_place.json(exclude_none=True, by_alias=True))
        d = await cls.Meta.trade_client.post('/orders', data=data)
        order = Order(**d)
        order._pending_place = True
        return order


    async def update_order(self, order_replace: OrderReplace):
        data = json.loads(order_replace.json(exclude_none=True, by_alias=True))
        try:
            self._change_request = order_replace
            self._pending_replace = True
            d = await self.Meta.trade_client.patch(f'/orders/{self.order_id}', data=data)
            self._replacing_order = Order(**d)
        except APIError as e:
            capture_exception(e)
            if e.status_code != 422:
                raise

    @property
    def replacing_order(self) -> typing.Optional[Order]:
        return self._replacing_order

    async def delete(self):
        self._pending_delete = True
        self._delete_req_at = datetime.datetime.now(tz=pytz.UTC)
        await self.Meta.trade_client.delete(f'/orders/{self.order_id}')

    @staticmethod
    async def delete_all():
        await Order.Meta.trade_client.delete('/orders')

    @property
    def pending_action(self) -> bool:
        return self._pending_delete or self._pending_replace or self._pending_place

    @property
    def pending_age(self) -> datetime.timedelta:
        if self._pending_replace:
            return self._change_request.age
        if self._pending_delete:
            return datetime.datetime.now(tz=pytz.UTC) - self._delete_req_at
        if self._pending_place:
            return self.age
        return datetime.timedelta(0)

    @classmethod
    async def get(cls: Order, status: str = None,
            limit: int = None,
            after: str = None,
            until: str = None,
            direction: str = None,
            params=None,
            nested: bool = None) -> typing.List[Order]:
        params = locals()
        params.pop('cls')
        return [Order(**x) for x in await Order.Meta.trade_client.get('/orders', params)]

    @property
    def net_qty(self) -> int:
        if self.side.is_sell:
            return -self.qty
        else:
            return self.qty

    @property
    def net_equity(self) -> float:
        return self.net_qty * self.limit_price

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
    async def get(cls: Account) -> Account:
        return Account(** await Account.Meta.trade_client.get('/account'))


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
    async def get(cls: Position) -> typing.List[Position]:
        dl = await cls.Meta.trade_client.get('/positions')
        return [Position(**x) for x in dl]

    @property
    def net_position(self) -> int:
        return self.qty

class Activity(aux.AplacaModel):
    activity_type: str
    id: str

    #@classmethod
    #async def get(cls: Activity, date: str = None, until: str = None, after: str = None, direction: str = 'desc',
    #              page_size: int = 100, page_token: str = None) -> typing.List[
    #    typing.Union[TradeActivity, NonTradeActivity]]:
    @classmethod
    async def get(cls: Activity, date: str = None, until: str = None, after: str = None, direction: str = 'desc',
                  page_size: int = 100, page_token: str = None) -> typing.List[
        typing.Union[TradeActivity, NonTradeActivity]]:

        d = locals()
        d.pop('cls')
        page_size_left = page_size
        dl = []
        tmp = []
        first = True
        url = '/account/activities'
        if cls == TradeActivity:
            url += '/FILL'
        while (page_size_left > 0 and len(tmp)>0) or first:
            d['page_size'] = min(page_size_left, 100)
            if not first:
                d['page_token'] = dl[-1]['id']
            tmp = await Activity.Meta.trade_client.get(url, data=d)
            dl.extend(tmp)
            page_size_left -= len(tmp)
            first = False
        return [TradeActivity(**d) if d['activity_type'] == 'FILL' else NonTradeActivity(**d) for d in dl]


    @property
    def is_trade(self) -> bool:
        return isinstance(self, TradeActivity)


class TradeActivity(Activity):
    cum_qty: int
    leaves_qty: int
    price: float
    qty: int
    side: ExtendedOrderSide
    symbol: str
    transaction_time: datetime.datetime
    order_id: str
    type: str

    @classmethod
    async def get(cls: Activity, date: str = None, until: str = None, after: str = None, direction: str = 'desc',
                  page_size: int = 100, page_token: str = None) -> typing.List[TradeActivity]:
        return await super().get(date, until, after, direction, page_size, page_token)


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
    async def get(cls: MarketClock) -> MarketClock:
        return MarketClock(** await cls.Meta.trade_client.get('/clock'))

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
