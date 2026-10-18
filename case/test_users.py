"""用户管理模块接口测试(与后端 routes/users.js 对应,均仅管理员可用)

- TestUsers:              无状态用例,JSON 数据驱动(data/users/users.json)
- TestUserManagementFlow: 链路用例(注册临时用户→查询→改角色→删除)
"""
import pytest

from api.auth_api import AuthApi
from api.users_api import UsersApi
from common.helpers import fill_sentinels
from common.read_json_data import read_json_data
from config import BASE_DIR


@pytest.fixture
def api():
    """用户管理模块接口对象"""
    return UsersApi()


def _resolve_token(token, client_token, merchant_token, admin_token):
    """把 token 字段里的占位符替换为真实 token"""
    return fill_sentinels({'token': token}, **{
        '#client_token#': client_token,
        '#merchant_token#': merchant_token,
        '#admin_token#': admin_token,
    })['token']


class TestUsers:
    """用户管理模块接口(无状态用例,JSON 数据驱动)"""

    data_path = f'{BASE_DIR}/data/users/users.json'
    cases, ids = read_json_data(data_path)

    @pytest.mark.parametrize('action,token,params,req_data,response',
                             cases, ids=ids)
    def test_users(self, api, client_token, merchant_token, admin_token,
                   action, token, params, req_data, response):
        token = _resolve_token(token, client_token, merchant_token, admin_token)

        if action == 'list':
            resp = api.list(token, **params)
        elif action == 'get':
            resp = api.get(params['id'], token)
        elif action == 'update_role':
            resp = api.update_role(params['id'], req_data, token)
        elif action == 'delete':
            resp = api.delete(params['id'], token)
        elif action == 'stats':
            resp = api.stats(token)
        else:
            raise ValueError(f'未知 action: {action}')

        assert resp.status_code == response['status_code'], resp.text
        body = resp.json()
        if response['status_code'] == 200:
            check = response.get('check')
            if check == 'non_empty':
                assert body['pagination']['total'] >= 1
                assert len(body['users']) >= 1
            elif check == 'empty':
                assert body['pagination']['total'] == 0
            elif check == 'all_role_admin':
                assert body['users']
                assert all(u['role'] == 'admin' for u in body['users'])
            elif check == 'detail':
                assert body['email'] == response['email']
                assert 'reservation_count' in body
            elif check == 'stats':
                assert 'total' in body and 'active' in body and 'totalUsers' in body
        else:
            # 400 参数校验失败:错误信息在 errors 数组;业务失败:在顶层 message 字段
            if 'errors' in body:
                actual_message = body['errors'][0]['msg']
            else:
                actual_message = body['message']
            assert actual_message == response['message'], resp.text


class TestUserManagementFlow:
    """用户管理链路(状态有依赖,按顺序执行)"""

    def test_user_lifecycle(self, admin_token, unique_email):
        """注册临时用户 → 管理员查询 → 改角色 → 删除 → 再查 404"""
        auth = AuthApi()
        api = UsersApi()

        # 注册一个临时用户(不污染种子账号)
        resp = auth.register(
            {'name': '临时用户', 'email': unique_email, 'password': 'pass123456'})
        assert resp.status_code == 201, resp.text
        user_id = resp.json()['user']['id']

        # 管理员按 ID 查询
        resp = api.get(user_id, admin_token)
        assert resp.status_code == 200, resp.text
        assert resp.json()['email'] == unique_email

        # 管理员改角色为 merchant
        resp = api.update_role(user_id, {'role': 'merchant'}, admin_token)
        assert resp.status_code == 200, resp.text
        resp = api.get(user_id, admin_token)
        assert resp.json()['role'] == 'merchant'

        # 管理员删除
        resp = api.delete(user_id, admin_token)
        assert resp.status_code == 200, resp.text
        assert resp.json()['message'] == '用户删除成功'

        # 删除后查询 → 404
        resp = api.get(user_id, admin_token)
        assert resp.status_code == 404
