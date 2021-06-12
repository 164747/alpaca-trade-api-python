from __future__ import annotations

import datetime
import logging
import typing
from dateutil.parser import parse
import pandas as pd
import pytz
from pydantic import BaseModel, Field, PrivateAttr

from alpaca_trade_api.models import aux

logger = logging.getLogger(__name__)

# _T = typing.TypeVar('_T')
_T = typing.ClassVar

StockSymbol = str


class Asset(aux.AplacaModel):
    asset_id: str = Field(alias='id')
    asset_class: str = Field(alias='class')
    symbol: str
    status: str
    tradable: bool
    marginable: bool
    shortable: bool
    easy_to_borrow: bool

    class Config:
        schema_extra = {
            'example':
                {
                    "id": "904837e3-3b76-47ec-b432-046db621571b",
                    "class": "us_equity",
                    "exchange": "NASDAQ",
                    "symbol": "AAPL",
                    "status": "active",
                    "tradable": True,
                    "marginable": True,
                    "shortable": True,
                    "easy_to_borrow": True
                }
        }

    @classmethod
    async def get(cls, symbol: str) -> Asset:
        return Asset(**await cls.Meta.trade_client.get(f'asset/{symbol}'))


class Bar(BaseModel):
    volume: int = Field(alias='v')
    open: float = Field(alias='o')
    close: float = Field(alias='c')
    high: float = Field(alias='h')
    low: float = Field(alias='l')
    utc_window_start: datetime.datetime = Field(alias='t')

    class Config:
        schema_extra = {
            'example':
                {
                    "t": "2021-02-01T16:01:00Z",
                    "o": 133.32,
                    "h": 133.74,
                    "l": 133.31,
                    "c": 133.5,
                    "v": 9876
                }
        }


class TickerWindow(aux.AplacaModel):
    symbol: str
    bars: typing.List[Bar]
    next_page_token: typing.Optional[str] = None
    _df: typing.Optional[pd.DataFrame] = PrivateAttr(default=None)

    class Config:
        schema_extra = {
            'example':
                {
                    "bars": [
                        {
                            "t": "2021-02-01T16:01:00Z",
                            "o": 133.32,
                            "h": 133.74,
                            "l": 133.31,
                            "c": 133.5,
                            "v": 9876
                        },
                        {
                            "t": "2021-02-01T16:02:00Z",
                            "o": 133.5,
                            "h": 133.58,
                            "l": 133.44,
                            "c": 133.58,
                            "v": 3567
                        }
                    ],
                    "symbol": "AAPL",
                    "next_page_token": "MjAyMS0wMi0wMVQxNDowMjowMFo7MQ=="
                }
        }

    @classmethod
    async def get(cls, symbol: str, start: str, end: str, limit: int = 10000, timeframe: str = '1Min',
                  page_token: str = None) -> TickerWindow:
        p = locals()
        p.pop('cls')
        p.pop('symbol')
        tw = TickerWindow(symbol=symbol, bars=[], next_page_token='')
        while tw.next_page_token is not None:
            tmp = TickerWindow(**await cls.Meta.data_client.get(f'/stocks/{symbol}/bars', api_version='v2', data=p))
            tw.consume(tmp)
            p['page_token'] = tw.next_page_token
        return tw

    @staticmethod
    async def get_start_end(symbol : str, end: typing.Union[str, datetime.datetime, None], delta: typing.Union[int, datetime.timedelta]) -> \
    typing.Tuple[str, str]:
        if end is None:
            end = (await IndividualTrade.get_latest(symbol)).trade.trade_time
        elif isinstance(end, str):
            end = parse(end)
        if isinstance(delta, int):
            delta = datetime.timedelta(days=delta)
        if end.tzinfo is None:
            end = end.replace(tzinfo=pytz.UTC)

        start = end - delta
        return start.replace(microsecond=0).isoformat(), end.replace(microsecond=0).isoformat()

    @classmethod
    async def get_by_td(cls, symbol: str, end: typing.Union[str, datetime.datetime] = None,
                        delta: typing.Union[int, datetime.timedelta] = 10, timeframe: str = '1Min') -> TickerWindow:
        start, end = await TickerWindow.get_start_end(symbol, end, delta)
        return await cls.get(symbol=symbol, start=start, end=end, timeframe=timeframe)

    def consume(self, other: TickerWindow):
        d_orig = {bar.utc_window_start: bar for bar in self.bars}
        d_orig.update({bar.utc_window_start: bar for bar in other.bars})
        self.bars = list(d_orig.values())
        self.bars.sort(key=lambda x: x.utc_window_start)
        self.next_page_token = other.next_page_token
        self._df = None

    @property
    def df(self) -> pd.DataFrame:
        if self._df is None:
            df = pd.DataFrame.from_dict(self.dict()['bars'])
            self._df = df.set_index('utc_window_start').sort_index()
        return self._df

    def add_bar(self, bar: Bar):
        if len(self.bars) == 0 or bar.utc_window_start > self.bars[-1].utc_window_start:
            logger.info(f'Adding BAR {bar} to {self.symbol}')
            self.bars.append(bar)
            self._df = None
        elif bar.utc_window_start == self.bars[-1].utc_window_start:
            self.bars[-1] = bar
        else:
            raise NotImplementedError


class TradeItem(BaseModel):
    original_id: typing.Optional[int] = Field(alias='i', default=None)
    exchange_id: typing.Optional[str] = Field(alias='x', default=None)
    price: float = Field(alias='p')
    size: int = Field(alias='s')
    trade_conditions: typing.Optional[typing.List[str]] = Field(alias='c', default=None)
    trade_time: datetime.datetime = Field(alias='t')
    tape: str = Field(alias='z')

    class Config:
        schema_extra = {'example': {
            "t": "2021-02-06T13:04:56.334320128Z",
            "x": "C",
            "p": 387.62,
            "s": 100,
            "c": [
                " ",
                "T"
            ],
            "i": 52983525029461,
            "z": "B"
        }}


class IndividualTrade(aux.AplacaModel):
    symbol: str
    trade: TradeItem

    @classmethod
    async def get_latest(cls, symbol: str) -> IndividualTrade:
        return IndividualTrade(**await cls.Meta.data_client.get(f'/stocks/{symbol}/trades/latest', api_version='v2'))


class Trade(aux.AplacaModel):
    symbol: str
    trades: typing.List[TradeItem]
    next_page_token: typing.Optional[str] = None

    _df: typing.Optional[pd.DataFrame] = PrivateAttr(default=None)

    @property
    def df(self) -> pd.DataFrame:
        if self._df is None:
            df = pd.DataFrame.from_dict(self.dict()['trades'])
            # df = df.set_index('trade_time').sort_index()
            self._df = df
        return self._df

    @property
    def size(self) -> int:
        return len(self.trades)

    def consume(self, other: Trade):
        print(self.next_page_token, len(self.trades))
        print(other.next_page_token, len(other.trades), '\n\n')

        self.trades.extend(other.trades)
        self.next_page_token = other.next_page_token
        self._df = None

    @classmethod
    async def get(cls, symbol: str, start: str, end: str, limit: int = 10000, page_token: str = None) -> Trade:
        p = locals()
        p.pop('cls')
        p.pop('symbol')
        t = Trade(symbol=symbol, trades=[], next_page_token='')
        while t.next_page_token is not None:
            t.consume(Trade(**await cls.Meta.data_client.get(f'/stocks/{symbol}/trades', api_version='v2', data=p)))
            p['page_token'] = t.next_page_token
            print(t.trades[-1], t.next_page_token)
        return t

    @classmethod
    async def get_by_td(cls, symbol: str, end: typing.Union[str, datetime.datetime] = None,
                        delta: typing.Union[int, datetime.timedelta] = 1) -> Trade:
        start, end = await TickerWindow.get_start_end(symbol, end, delta)
        return await cls.get(symbol, start, end)
