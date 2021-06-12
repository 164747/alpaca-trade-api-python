import asyncio
import json
import logging
import os

import aiohttp

from .common import (
    get_base_url,
    get_credentials,
    get_api_version, URL, )

logger = logging.getLogger(__name__)


class RetryException(Exception):
    pass


class APIError(Exception):
    """
    Represent API related error.
    error.status_code will have http status code.
    """

    def __init__(self, error: dict, http_error: aiohttp.ClientResponseError):
        super().__init__(error['message'])
        self._error = error
        self._http_error = http_error

    @property
    def code(self):
        return self._error['code']

    @property
    def status_code(self):
        return self._http_error.status


class REST(object):
    def __init__(self,
                 key_id: str = None,
                 secret_key: str = None,
                 base_url: URL = None,
                 api_version: str = None,
                 oauth=None
                 ):
        self._key_id, self._secret_key, self._oauth = get_credentials(
            key_id, secret_key, oauth)
        self._base_url: URL = URL(base_url or get_base_url())
        self._api_version = get_api_version(api_version)
        # self._session = requests.Session()
        self._session = aiohttp.ClientSession()
        self._retry = int(os.environ.get('APCA_RETRY_MAX', 3))
        self._retry_wait = int(os.environ.get('APCA_RETRY_WAIT', 3))
        self._retry_codes = [int(o) for o in os.environ.get(
            'APCA_RETRY_CODES', '429,504').split(',')]

    async def _request(self,
                       method,
                       path,
                       data=None,
                       base_url: URL = None,
                       api_version: str = None
                       ):
        logger.info(f'REQUEST {method} {path} {data}')
        base_url = base_url or self._base_url
        version = api_version if api_version else self._api_version
        url: URL = URL(base_url + '/' + version + path)
        headers = {}
        if self._oauth:
            headers['Authorization'] = 'Bearer ' + self._oauth
        else:
            headers['APCA-API-KEY-ID'] = self._key_id
            headers['APCA-API-SECRET-KEY'] = self._secret_key
        opts = {
            'headers': headers,
            # Since we allow users to set endpoint URL via env var,
            # human error to put non-SSL endpoint could exploit
            # uncanny issues in non-GET request redirecting http->https.
            # It's better to fail early if the URL isn't right.
            'allow_redirects': False,
        }
        if method.upper() == 'GET':
            opts['params'] = data
        else:
            opts['json'] = data

        retry = self._retry
        if retry < 0:
            retry = 0
        while retry >= 0:
            try:
                return await self._one_request(method, url, opts, retry)
            except RetryException:
                retry_wait = self._retry_wait
                logger.warning(
                    'sleep {} seconds and retrying {} '
                    '{} more time(s)...'.format(
                        retry_wait, url, retry))
                await asyncio.sleep(retry_wait)
                # time.sleep(retry_wait)
                retry -= 1
                continue

    async def _one_request(self, method: str, url: URL, opts: dict, retry: int):
        """
        Perform one request, possibly raising RetryException in the case
        the response is 429. Otherwise, if error text contain "code" string,
        then it decodes to json object and returns APIError.
        Returns the body json in the 200 status.
        """
        retry_codes = self._retry_codes
        resp = await self._session.request(method, url, timeout=None, **opts)
        body = await resp.text()
        try:
            resp.raise_for_status()
        # except HTTPError as http_error:
        except aiohttp.ClientResponseError as http_error:
            if resp.status in retry_codes and retry > 0:
                raise RetryException()
            try:
                error_dict = json.loads(body)
                raise APIError(error_dict, http_error)
            except json.JSONDecodeError:
                raise http_error
        if await resp.text() != '':
            return await resp.json()
        return None

    async def get(self, path, api_version : str=None, data: dict = None):
        d = data
        if data is not None:
            d = {k: v for k, v in data.items() if v is not None}
        return await self._request('GET', path, d, api_version=api_version)

    async def post(self, path, data=None):
        return await self._request('POST', path, data)

    async def put(self, path, data=None):
        return await self._request('PUT', path, data)

    async def patch(self, path, data=None):
        return await self._request('PATCH', path, data)

    async def delete(self, path, data=None):
        return await self._request('DELETE', path, data)

    def __enter__(self):
        return self

    def close(self):
        self._session.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
