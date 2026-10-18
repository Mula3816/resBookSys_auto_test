"""HTTP 请求封装:统一拼接 base_url,后续扩展日志/重试都加在这里"""
import requests

import config


class RequestClient:
    """简单的 requests 封装,请求路径只需传相对路径"""

    def __init__(self, base_url: str = None, timeout: int = 10):
        self.base_url = (base_url or config.BASE_URL).rstrip('/')
        self.timeout = timeout

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        kwargs.setdefault('timeout', self.timeout)
        return requests.request(method, f'{self.base_url}{path}', **kwargs)
