"""餐厅模块接口封装(与后端 routes/restaurants.js 对应)

- GET    /api/restaurants                   餐厅列表(公开,分页/筛选)
- GET    /api/restaurants/stats             餐厅统计(公开)
- GET    /api/restaurants/:id               餐厅详情(公开,含桌台)
- GET    /api/restaurants/:id/availability  餐厅可用时段(公开)
- POST   /api/restaurants                   创建餐厅(商家/管理员,支持图片上传)
- PUT    /api/restaurants/:id               更新餐厅(商家/管理员)
- DELETE /api/restaurants/:id               删除餐厅(商家/管理员)
"""
from common.request_client import RequestClient


class RestaurantsApi:
    """餐厅订位系统餐厅模块接口"""

    PATH = '/api/restaurants'

    def __init__(self, client: RequestClient = None):
        self.client = client or RequestClient()

    @staticmethod
    def _headers(token: str) -> dict:
        return {'Authorization': f'Bearer {token}'} if token else {}

    # ---- 公开接口(无需鉴权) ----

    def list(self, **params):
        """餐厅列表,params 为查询参数(page/limit/search/cuisine_type 等)"""
        return self.client.request('GET', self.PATH, params=params)

    def stats(self, **params):
        """餐厅统计(可选 owner_id)"""
        return self.client.request('GET', f'{self.PATH}/stats', params=params)

    def get(self, restaurant_id):
        """餐厅详情(含桌台列表)"""
        return self.client.request('GET', f'{self.PATH}/{restaurant_id}')

    def availability(self, restaurant_id, **params):
        """餐厅可用时段(date 必填,party_size 可选)"""
        return self.client.request(
            'GET', f'{self.PATH}/{restaurant_id}/availability', params=params)

    # ---- 商家/管理员 ----

    def create(self, req_data: dict, token: str, files: dict = None):
        """创建餐厅;files 提供时走 multipart(图片上传),否则 JSON"""
        headers = self._headers(token)
        if files:
            return self.client.request(
                'POST', self.PATH, headers=headers, data=req_data, files=files)
        return self.client.request(
            'POST', self.PATH, headers=headers, json=req_data)

    def update(self, restaurant_id, req_data: dict, token: str,
               files: dict = None):
        """更新餐厅(商家仅限自己的店;files 提供时走 multipart)"""
        headers = self._headers(token)
        if files:
            return self.client.request(
                'PUT', f'{self.PATH}/{restaurant_id}',
                headers=headers, data=req_data, files=files)
        return self.client.request(
            'PUT', f'{self.PATH}/{restaurant_id}', headers=headers,
            json=req_data)

    def delete(self, restaurant_id, token: str):
        """删除餐厅(商家仅限自己的店)"""
        return self.client.request(
            'DELETE', f'{self.PATH}/{restaurant_id}',
            headers=self._headers(token))
