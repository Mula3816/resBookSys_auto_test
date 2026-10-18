"""预定模块接口封装(与后端 routes/reservations.js 对应)

- GET    /api/reservations                 预订列表(分页/筛选)
- POST   /api/reservations                 创建预订
- GET    /api/reservations/:id             预订详情(含状态历史)
- PUT    /api/reservations/:id/status      更新状态(商家/管理员)
- PUT    /api/reservations/:id/cancel      取消预订(本人或管理员)
- PUT    /api/reservations/:id/payment     登记付款(商家/管理员)
- DELETE /api/reservations/:id             删除预订(商家/管理员)
"""
from common.request_client import RequestClient


class ReservationsApi:
    """餐厅订位系统预定模块接口"""

    PATH = '/api/reservations'

    def __init__(self, client: RequestClient = None):
        self.client = client or RequestClient()

    @staticmethod
    def _headers(token: str) -> dict:
        return {'Authorization': f'Bearer {token}'} if token else {}

    def list(self, token: str, **params):
        """预订列表,params 为查询参数(page/limit/status/restaurant_id 等)"""
        return self.client.request(
            'GET', self.PATH, headers=self._headers(token), params=params)

    def get(self, reservation_id, token: str):
        """预订详情(含状态变更历史)"""
        return self.client.request(
            'GET', f'{self.PATH}/{reservation_id}',
            headers=self._headers(token))

    def create(self, req_data: dict, token: str):
        """创建预订"""
        return self.client.request(
            'POST', self.PATH, headers=self._headers(token), json=req_data)

    def update_status(self, reservation_id, req_data: dict, token: str):
        """更新预订状态(仅商家/管理员)"""
        return self.client.request(
            'PUT', f'{self.PATH}/{reservation_id}/status',
            headers=self._headers(token), json=req_data)

    def cancel(self, reservation_id, req_data: dict, token: str):
        """取消预订(仅本人或管理员)"""
        return self.client.request(
            'PUT', f'{self.PATH}/{reservation_id}/cancel',
            headers=self._headers(token), json=req_data)

    def payment(self, reservation_id, req_data: dict, token: str):
        """登记付款(仅商家/管理员,预订须为 completed)"""
        return self.client.request(
            'PUT', f'{self.PATH}/{reservation_id}/payment',
            headers=self._headers(token), json=req_data)

    def delete(self, reservation_id, token: str):
        """删除预订(仅商家/管理员,预订须为 completed/cancelled)"""
        return self.client.request(
            'DELETE', f'{self.PATH}/{reservation_id}',
            headers=self._headers(token))

    def stats(self, token: str):
        """预订统计仪表盘(仅商家/管理员)"""
        return self.client.request(
            'GET', f'{self.PATH}/stats/dashboard',
            headers=self._headers(token))
