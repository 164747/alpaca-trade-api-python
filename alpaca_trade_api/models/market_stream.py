import datetime
import typing

import pytz
from pydantic import BaseModel, Field

from polygon.rest import rest_models


class SocketBase(BaseModel):
    symbol: str = Field(alias='S')
    event_type: str = Field(alias='t')


class Trade(SocketBase):
    exchange_id: int = Field(alias='x')
    trade_id: int = Field(alias='i')
    tape: int = Field(alias='z')
    price: float = Field(alias='p')
    size: int = Field(alias='s')
    trade_conditions: typing.List[int] = Field(alias='c', default=None)
    utc: datetime.datetime = Field(alias='t')

    class Config:
        schema_extra = {
            'example': {
                "T": "t",
                "i": 96921,
                "S": "AAPL",
                "x": "D",
                "p": 126.55,
                "s": 1,
                "t": "2021-02-22T15:51:44.208Z",
                "c": [
                    "@",
                    "I"
                ],
                "z": "C"
            }
        }

    @property
    def age(self) -> datetime.timedelta:
        return datetime.datetime.now(pytz.utc) - self.utc

    @property
    def trade_item(self) -> rest_models.TradeItem:
        return rest_models.TradeItem(**self.dict())


class Quote(SocketBase):
    bid_exchange_id: typing.Optional[int] = Field(alias='bx', default=None)
    bid_price: typing.Optional[float] = Field(alias='bp', default=None)
    bid_size: typing.Optional[int] = Field(alias='bs', default=None)
    ask_exchange_id: typing.Optional[int] = Field(alias='ax', default=None)
    ask_price: typing.Optional[float] = Field(alias='ap', default=None)
    ask_size: typing.Optional[int] = Field(alias='as', default=None)
    quote_conditions: typing.Optional[int] = Field(alias='c', default=None)
    utc: datetime.datetime = Field(alias='t')

    class Config:
        schema_extra = {'example': {
            "T": "q",
            "S": "AMD",
            "bx": "U",
            "bp": 87.66,
            "bs": 1,
            "ax": "Q",
            "ap": 87.68,
            "as": 4,
            "t": "2021-02-22T15:51:45.335689322Z",
            "c": [
                "R"
            ],
            "z": "C"
        }}

    def __str__(self):
        return f'{self.bid_size}:{self.bid_price} -- {self.ask_size}:{self.ask_price}'

    @property
    def is_complete(self) -> bool:
        return self.bid_price is not None and self.ask_price is not None

    @property
    def age(self) -> datetime.timedelta:
        return datetime.datetime.now(pytz.utc) - self.utc

    @property
    def payback(self) -> float:
        return (self.bid_price / self.ask_price) ** .5

    @property
    def middle_price(self) -> float:
        return (self.ask_price + self.bid_price) / 2.0


class Bar(SocketBase):
    volume: int = Field(alias='v')
    volume_today: int = Field(alias='av')
    official_open_price: float = Field(alias='op')
    vol_weight_price: float = Field(alias='vw')
    open_price: float = Field(alias='o')
    close_price: float = Field(alias='c')
    high_price: float = Field(alias='h')
    low_price: float = Field(alias='l')
    avg_prive: float = Field(alias='a')
    utc_start: datetime.datetime = Field(alias='s')
    utc_end: datetime.datetime = Field(alias='e')

    class Config:
        schema_extra = {'example': {
            "T": "b",
            "S": "SPY",
            "o": 388.985,
            "h": 389.13,
            "l": 388.975,
            "c": 389.12,
            "v": 49378,
            "t": "2021-02-22T19:15:00Z"
        }}

    @property
    def rest_bar(self) -> rest_models.Bar:
        return rest_models.Bar(v=self.volume, o=self.open_price, c=self.close_price, h=self.high_price,
                               l=self.low_price,
                               t=self.utc_start, n=1)
