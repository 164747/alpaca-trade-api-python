import requests

from alpaca_trade_api.common import get_polygon_credentials, URL


class REST(object):

    def __init__(self, api_key: str, staging: bool = False):
        self._api_key: str = get_polygon_credentials(api_key)
        self._staging: bool = staging
        self._session = requests.Session()

    def _request(self, method: str, path: str, params: dict = None,
                 version: str = 'v1'):
        """
        :param method: GET, POST, ...
        :param path: url part path (without the domain name)
        :param params: dictionary with params of the request
        :param version: v1 or v2
        :return: response
        """
        url: URL = URL('https://api.polygon.io/' + version + path)
        params = params or {}
        params['apiKey'] = self._api_key
        if self._staging:
            params['apiKey'] += '-staging'
        resp = self._session.request(method, url, params=params)
        resp.raise_for_status()
        return resp.json()

    def get(self, path: str, params: dict = None, version: str = 'v1'):
        return self._request('GET', path, params=params, version=version)

