"""用户管理模块接口封装(与后端 routes/users.js 对应,均仅管理员可用)

- GET    /api/users          用户列表(分页/角色/搜索)
- GET    /api/users/:id      用户详情(含预订数)
- PUT    /api/users/:id/role 更新用户角色
- DELETE /api/users/:id      删除用户
"""
from common.request_client import RequestClient


class UsersApi:
    """餐厅订位系统用户管理模块接口"""

    PATH = '/api/users'

    def __init__(self, client: RequestClient = None):
        self.client = client or RequestClient()

    @staticmethod
    def _headers(token: str) -> dict:
        return {'Authorization': f'Bearer {token}'} if token else {}

    def list(self, token: str, **params):
        """用户列表,params 为查询参数(page/limit/role/search)"""
        return self.client.request(
            'GET', self.PATH, headers=self._headers(token), params=params)

    def get(self, user_id, token: str):
        """用户详情(含预订数)"""
        return self.client.request(
            'GET', f'{self.PATH}/{user_id}', headers=self._headers(token))

    def update_role(self, user_id, req_data: dict, token: str):
        """更新用户角色"""
        return self.client.request(
            'PUT', f'{self.PATH}/{user_id}/role',
            headers=self._headers(token), json=req_data)

    def delete(self, user_id, token: str):
        """删除用户"""
        return self.client.request(
            'DELETE', f'{self.PATH}/{user_id}', headers=self._headers(token))

    def stats(self, token: str):
        """用户统计仪表盘(仅管理员)"""
        return self.client.request(
            'GET', f'{self.PATH}/stats/dashboard',
            headers=self._headers(token))
