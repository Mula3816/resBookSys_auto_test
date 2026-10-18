"""预定模块接口测试(与后端 routes/reservations.js 对应)

- TestReservations:       无状态用例,JSON 数据驱动(data/reservations/reservations.json)
- TestReservationFlow:    生命周期链路用例(创建→详情→改状态→付款→删除 / 取消流程)
"""
import pytest

import config
from api.reservations_api import ReservationsApi
from common.db_cleaner import clean_flow_reservations
from common.helpers import fill_sentinels
from common.read_json_data import read_json_data
from config import BASE_DIR

# 链路用例的预订日期(在 config 统一管理,数据清理 fixture 按此日期清理)
LIFECYCLE_DATE, CANCEL_DATE = config.FLOW_RESERVATION_DATES


@pytest.fixture
def api():
    """预定模块接口对象"""
    return ReservationsApi()


def _resolve_token(token, client_token, merchant_token, admin_token):
    """把 token 字段里的占位符替换为真实 token"""
    return fill_sentinels({'token': token}, **{
        '#client_token#': client_token,
        '#merchant_token#': merchant_token,
        '#admin_token#': admin_token,
    })['token']


class TestReservations:
    """预定模块接口(无状态用例,JSON 数据驱动)"""

    data_path = f'{BASE_DIR}/data/reservations/reservations.json'
    cases, ids = read_json_data(data_path)

    @pytest.mark.parametrize('action,token,params,req_data,response',
                             cases, ids=ids)
    def test_reservations(self, api, client_token, merchant_token, admin_token,
                          action, token, params, req_data, response):
        token = _resolve_token(token, client_token, merchant_token, admin_token)

        if action == 'list':
            resp = api.list(token, **params)
        elif action == 'get':
            resp = api.get(params['id'], token)
        elif action == 'create':
            resp = api.create(req_data, token)
        elif action == 'update_status':
            resp = api.update_status(params['id'], req_data, token)
        elif action == 'cancel':
            resp = api.cancel(params['id'], req_data, token)
        elif action == 'payment':
            resp = api.payment(params['id'], req_data, token)
        elif action == 'delete':
            resp = api.delete(params['id'], token)
        elif action == 'stats':
            resp = api.stats(token)
        else:
            raise ValueError(f'未知 action: {action}')

        assert resp.status_code == response['status_code'], resp.text
        body = resp.json()
        if response['status_code'] == 200:
            if response.get('check') == 'non_empty':
                assert body['pagination']['total'] >= 1
                assert len(body['reservations']) >= 1
            elif response.get('check') == 'empty':
                assert body['pagination']['total'] == 0
                assert body['reservations'] == []
            elif response.get('check') == 'has_history':
                assert isinstance(body.get('history'), list)
            elif response.get('check') == 'stats':
                assert 'total' in body and 'revenue' in body and 'changes' in body
            else:
                assert body['message'] == response['message']
        else:
            # 400 参数校验失败:错误信息在 errors 数组;业务失败:在顶层 message 字段
            if 'errors' in body:
                actual_message = body['errors'][0]['msg']
            else:
                actual_message = body['message']
            assert actual_message == response['message'], resp.text


class TestReservationFlow:
    """预订全生命周期链路(状态有依赖,按顺序执行)"""

    def test_reservation_lifecycle(self, client_token, merchant_token):
        """创建 → 详情 → 商家确认/完成 → 登记付款 → 删除 → 再查 404"""
        api = ReservationsApi()

        # 自愈:清掉上次运行/重试残留的预订(pending 无法通过 API 删除)
        clean_flow_reservations()

        # 1. 客户创建预订(桌台 12 容量 8,日期为未来,避开种子数据)
        resp = api.create({
            'restaurant_id': 1, 'table_id': 12,
            'reservation_date': LIFECYCLE_DATE, 'reservation_time': '19:00',
            'party_size': 4, 'occasion': '生日聚会', 'special_requests': '靠窗座位'
        }, client_token)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        reservation_id = body['reservationId']
        assert body['message'] == '预订创建成功'
        assert body['confirmationCode']

        # 2. 本人查看详情(含状态历史)
        resp = api.get(reservation_id, client_token)
        assert resp.status_code == 200, resp.text
        detail = resp.json()
        assert detail['status'] == 'pending'
        assert detail['party_size'] == 4
        assert isinstance(detail['history'], list)

        # 3. 商家确认 → 完成
        for status in ('confirmed', 'completed'):
            resp = api.update_status(reservation_id, {'status': status},
                                     merchant_token)
            assert resp.status_code == 200, resp.text

        # 4. 商家登记付款
        resp = api.payment(reservation_id,
                           {'total_amount': 268.5, 'payment_method': '微信支付'},
                           merchant_token)
        assert resp.status_code == 200, resp.text
        assert resp.json()['payment']['total_amount'] == 268.5

        # 5. 商家删除(仅已完成/已取消可删)
        resp = api.delete(reservation_id, merchant_token)
        assert resp.status_code == 200, resp.text
        assert resp.json()['message'] == '预订删除成功'

        # 6. 删除后再查 → 404
        resp = api.get(reservation_id, client_token)
        assert resp.status_code == 404

    def test_reservation_cancel_flow(self, client_token):
        """创建 → 本人取消 → 重复取消 400"""
        api = ReservationsApi()

        # 自愈:清掉上次运行/重试残留的预订(pending 无法通过 API 删除)
        clean_flow_reservations()

        resp = api.create({
            'restaurant_id': 1, 'table_id': 11,
            'reservation_date': CANCEL_DATE, 'reservation_time': '19:00',
            'party_size': 4
        }, client_token)
        assert resp.status_code == 201, resp.text
        reservation_id = resp.json()['reservationId']

        resp = api.cancel(reservation_id, {'reason': '行程变更'}, client_token)
        assert resp.status_code == 200, resp.text
        assert resp.json()['message'] == '预订取消成功'

        resp = api.cancel(reservation_id, {}, client_token)
        assert resp.status_code == 400
        assert resp.json()['message'] == '该预订已取消'
