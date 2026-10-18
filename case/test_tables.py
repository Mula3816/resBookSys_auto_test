"""桌台模块接口测试(与后端 routes/tables.js 对应)

- TestTables: 无状态用例,JSON 数据驱动(data/tables/tables.json)
- 桌台的增删改链路在 test_restaurants.py 的餐厅生命周期用例中覆盖
"""
import pytest

from api.tables_api import TablesApi
from common.helpers import fill_sentinels
from common.read_json_data import read_json_data
from config import BASE_DIR


@pytest.fixture
def api():
    """桌台模块接口对象"""
    return TablesApi()


def _resolve_token(token, client_token, merchant_token, admin_token):
    """把 token 字段里的占位符替换为真实 token;游客(#guest#)替换为空"""
    return fill_sentinels({'token': token}, **{
        '#guest#': '',
        '#client_token#': client_token,
        '#merchant_token#': merchant_token,
        '#admin_token#': admin_token,
    })['token']


class TestTables:
    """桌台模块接口(无状态用例,JSON 数据驱动)"""

    data_path = f'{BASE_DIR}/data/tables/tables.json'
    cases, ids = read_json_data(data_path)

    @pytest.mark.parametrize('action,token,params,req_data,response',
                             cases, ids=ids)
    def test_tables(self, api, client_token, merchant_token, admin_token,
                    action, token, params, req_data, response):
        token = _resolve_token(token, client_token, merchant_token, admin_token)

        if action == 'list':
            resp = api.list(**params)
        elif action == 'get':
            resp = api.get(params['id'])
        elif action == 'availability':
            resp = api.availability(
                params['id'], **{k: v for k, v in params.items() if k != 'id'})
        elif action == 'create':
            resp = api.create(req_data, token)
        elif action == 'update':
            resp = api.update(params['id'], req_data, token)
        elif action == 'delete':
            resp = api.delete(params['id'], token)
        else:
            raise ValueError(f'未知 action: {action}')

        assert resp.status_code == response['status_code'], resp.text
        body = resp.json()
        if response['status_code'] == 200:
            check = response.get('check')
            if check == 'non_empty':
                assert len(body['tables']) >= 1
            elif check == 'empty':
                assert body['tables'] == []
            elif check == 'detail':
                assert body['table']['id'] == params['id']
            elif check == 'has_unavailable_slot':
                # 种子预订(19:00)使 2 小时窗口内的时段不可用
                assert isinstance(body['availability'], list)
                assert any(slot['available'] is False
                           for slot in body['availability'])
        else:
            # 400 参数校验失败:错误信息在 errors 数组;业务失败:在顶层 message 字段
            if 'errors' in body:
                actual_message = body['errors'][0]['msg']
            else:
                actual_message = body['message']
            assert actual_message == response['message'], resp.text
