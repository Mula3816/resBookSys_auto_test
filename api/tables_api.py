"""桌台模块接口封装(与后端 routes/tables.js 对应)

- GET    /api/tables                   桌台列表(公开,可按餐厅/状态筛选)
- GET    /api/tables/:id               桌台详情(公开)
- GET    /api/tables/:id/availability  桌台可用时段(公开,date 必填)
- POST   /api/tables                   创建桌台(商家/管理员)
- PUT    /api/tables/:id               更新桌台(商家/管理员)
- DELETE /api/tables/:id               删除桌台(商家/管理员,有有效预订不可删)
"""
from common.request_client import RequestClient


class TablesApi:
    """餐厅订位系统桌台模块接口"""

    PATH = '/api/tables'

    def __init__(self, client: RequestClient = None):
        self.client = client or RequestClient()

    @staticmethod
    def _headers(token: str) -> dict:
        return {'Authorization': f'Bearer {token}'} if token else {}

    # ---- 公开接口(无需鉴权) ----

    def list(self, **params):
        """桌台列表,params 为查询参数(restaurant_id/status/search 等)"""
        return self.client.request('GET', self.PATH, params=params)

    def get(self, table_id):
        """桌台详情"""
        return self.client.request('GET', f'{self.PATH}/{table_id}')

    def availability(self, table_id, **params):
        """桌台可用时段(date 必填)"""
        return self.client.request(
            'GET', f'{self.PATH}/{table_id}/availability', params=params)

    # ---- 商家/管理员 ----

    def create(self, req_data: dict, token: str):
        """创建桌台(商家仅限自己的餐厅)"""
        return self.client.request(
            'POST', self.PATH, headers=self._headers(token), json=req_data)

    def update(self, table_id, req_data: dict, token: str):
        """更新桌台(商家仅限自己餐厅的桌台)"""
        return self.client.request(
            'PUT', f'{self.PATH}/{table_id}',
            headers=self._headers(token), json=req_data)

    def delete(self, table_id, token: str):
        """删除桌台(商家仅限自己餐厅的桌台,有有效预订不可删)"""
        return self.client.request(
            'DELETE', f'{self.PATH}/{table_id}', headers=self._headers(token))
