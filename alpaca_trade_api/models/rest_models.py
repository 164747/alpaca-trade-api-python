from __future__ import annotations

import datetime
import typing
from enum import Enum

import pytz
from pydantic import Field

from alpaca_trade_api.models import aux


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
    limit_price: typing.Optional[float] = None
    stop_price: typing.Optional[float] = None
    extended_hours: bool = False
    trail_price: typing.Optional[float] = None
    trail_percent: typing.Optional[float] = None
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
    hwm: float

    @property
    def unmatched_qty(self) -> int:
        return self.qty - self.filled_qty

    @classmethod
    def place_order(cls : Order, order_place: OrderPlace) -> Order:
        d = cls.Meta.client.post('/order', data=order_place.dict())
        return Order(**d)

    def update_order(self, order_replace: OrderReplace) -> Order:
        d = self.client.patch(f'/order/{self.order_id}', data=order_replace.dict())
        return Order(**d)

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
    is_open : bool
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

