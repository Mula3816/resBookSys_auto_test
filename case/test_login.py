"""登录模块接口测试

覆盖认证模块三个接口:
- POST /api/auth/register  注册
- POST /api/auth/login     登录
- GET  /api/auth/me        当前用户(token 鉴权)
"""
import pytest

from api.auth_api import AuthApi
from common.helpers import fill_sentinels
from common.read_json_data import read_json_data
from config import BASE_DIR

@pytest.fixture
def auth():
    """认证模块接口对象"""
    return AuthApi()


class TestLogin:
    """POST /api/auth/login 登录接口"""

    # 下面是登录的参数化测试,用 JSON 文件驱动
    login_data_path = f'{BASE_DIR}/data/auth/login.json'
    login_params, login_ids = read_json_data(login_data_path)

    @pytest.mark.parametrize('req_data,response', login_params, ids=login_ids)
    def test_login(self, auth, req_data, response):
        resp = auth.login(req_data)
        assert resp.status_code == response['status_code'], resp.text
        # 400 参数校验失败:错误信息在 errors 数组;401 凭证错误:在 message 字段
        if response['status_code'] == 200:
            body = resp.json()
            assert body['token']
            assert body['message'] == response['message']
            assert body['user']['email'] == req_data['email']
            assert body['user']['role'] == response['role'] 
        elif response['status_code'] == 400:
            actual_message = resp.json()['errors'][0]['msg']
            assert actual_message == response['message']
        else:
            actual_message = resp.json()['message']
            assert actual_message == response['message']

    # 下面是登录成功+登录失败的原写法，已参数化为上面的形式
    '''
    @pytest.mark.parametrize('account', ['client', 'merchant'])
        def test_login_success(self, auth, test_accounts, account):
            """正确邮箱+正确密码 → 200,返回 token 和用户信息"""
            info = test_accounts[account]
            req_data = {'email': info['email'], 'password': info['password']}
            resp = auth.login(req_data)
            assert resp.status_code == 200, resp.text
            body = resp.json()
            print('登录返回:', body)
            assert body['message'] == '登录成功'
            assert body['token']
            assert body['user']['email'] == info['email']
            assert body['user']['role'] == info['role']
    
        # 下面是登录失败的参数化测试,用 JSON 文件驱动
        login_fail_data_path = f'{BASE_DIR}/data/login_fail_cases.json'
        login_fail_params, login_fail_ids = read_json_data(login_fail_data_path)
    
        @pytest.mark.parametrize('req_data,status_code,message',
                                 login_fail_params, ids=login_fail_ids)
        def test_login_fail(self, auth, req_data, status_code, message):
            resp = auth.login(req_data)
            assert resp.status_code == status_code, resp.text
            # 400 参数校验失败:错误信息在 errors 数组;401 凭证错误:在 message 字段
            if status_code == 400:
                actual_message = resp.json()['errors'][0]['msg']
            else:
                actual_message = resp.json()['message']
            assert actual_message == message
    '''
    
    # 下面注释的是登录失败原写法，已参数化为上面的形式
    '''
    def test_login_wrong_password(self, auth, test_accounts):
        """已注册邮箱+错误密码 → 401"""
        info = test_accounts['client']
        resp = auth.login(info['email'], 'wrong_password_123')
        print("""已注册邮箱+错误密码 → 401""",resp.json())
        assert resp.status_code == 401, resp.text
        assert resp.json()['message'] == '账号或密码错误'

    def test_login_unregistered_email(self, auth):
        """未注册邮箱 → 401(与密码错误同文案,防止账号枚举)"""
        resp = auth.login('nobody_404@example.com', 'whatever123')
        print("""未注册邮箱 → 401""",resp.json())
        assert resp.status_code == 401, resp.text
        assert resp.json()['message'] == '账号或密码错误'

    @pytest.mark.parametrize('email', [
        'not-an-email', 'abc@', 'abc@@x.com', '',
    ], ids=['无@符号', '无域名', '双@', '空字符串'])
    def test_login_invalid_email_format(self, auth, email):
        """邮箱格式非法 → 400,返回 errors 数组"""
        resp = auth.login(email, 'password123')
        print("""邮箱格式非法 → 400""",resp.json())
        assert resp.status_code == 400, resp.text
        assert 'errors' in resp.json()

    def test_login_empty_password(self, auth, test_accounts):
        """密码为空串 → 400"""
        resp = auth.login(test_accounts['client']['email'], '')
        print("""密码为空串 → 400""",resp.json())
        assert resp.status_code == 400, resp.text
        assert 'errors' in resp.json()

    def test_login_missing_password(self, auth, test_accounts):
        """请求体缺少密码字段 → 400"""
        resp = auth.client.request(
            'POST', f'{AuthApi.PATH}/login',
            json={'email': test_accounts['client']['email']})
        print("""请求体缺少密码字段 → 400""",resp.json())
        assert resp.status_code == 400, resp.text

    def test_login_missing_email(self, auth, test_accounts):
        """请求体缺少邮箱字段 → 400"""
        resp = auth.client.request(
            'POST', f'{AuthApi.PATH}/login',
            json={'password': test_accounts['client']['password']})
        print("""请求体缺少邮箱字段 → 400""",resp.json())
        assert resp.status_code == 400, resp.text

    def test_login_empty_body(self, auth):
        """空请求体 → 400"""
        resp = auth.client.request('POST', f'{AuthApi.PATH}/login', json={})
        print("""空请求体 → 400""",resp.json())
        assert resp.status_code == 400, resp.text
        '''


class TestRegister:
    """POST /api/auth/register 注册接口"""

    register_data_path = f'{BASE_DIR}/data/auth/register.json'
    register_params, register_ids = read_json_data(register_data_path)

    @pytest.mark.parametrize('req_data,response', register_params, ids=register_ids)
    def test_register(self, auth, unique_email, req_data, response):
        req_data = fill_sentinels(req_data, **{'#unique_email#': unique_email})
        resp = auth.register(req_data)
        assert resp.status_code == response['status_code'], resp.text
        body = resp.json()
        if response['status_code'] == 201:
            assert body['message'] == response['message']
            assert body['token']
            assert body['user']['email'] == req_data['email']
            assert body['user']['role'] == response['role']
            # then_login: 注册成功后立即用新账号登录(完整链路)
            if response.get('then_login'):
                login_resp = auth.login(
                    {'email': req_data['email'],
                     'password': req_data['password']})
                assert login_resp.status_code == 200, login_resp.text
                assert login_resp.json()['user']['id'] == body['user']['id']
        else:
            # 400 参数校验失败:错误信息在 errors 数组;邮箱重复:在顶层 message 字段
            if 'errors' in body:
                actual_message = body['errors'][0]['msg']
            else:
                actual_message = body['message']
            assert actual_message == response['message']


class TestMe:
    """GET /api/auth/me 当前用户接口(token 鉴权)"""

    me_data_path = f'{BASE_DIR}/data/auth/me.json'
    me_params, me_ids = read_json_data(me_data_path)

    @pytest.mark.parametrize('req_data,response', me_params, ids=me_ids)
    def test_me(self, auth, client_token, req_data, response):
        req_data = fill_sentinels(req_data, **{'#login_token#': client_token})
        resp = auth.me(req_data)
        assert resp.status_code == response['status_code'], resp.text
        body = resp.json()
        if response['status_code'] == 200:
            assert body['user']['email'] == response['email']
            assert 'stats' in body['user']
        else:
            assert body['message'] == response['message']


class TestProfile:
    """PUT /api/auth/profile 个人资料接口"""

    profile_data_path = f'{BASE_DIR}/data/auth/profile.json'
    profile_params, profile_ids = read_json_data(profile_data_path)

    @pytest.mark.parametrize('token,req_data,response', profile_params,
                             ids=profile_ids)
    def test_profile(self, auth, client_token, token, req_data, response):
        token = fill_sentinels(
            {'token': token}, **{'#client_token#': client_token})['token']
        resp = auth.profile(req_data, token)
        assert resp.status_code == response['status_code'], resp.text
        body = resp.json()
        if response['status_code'] == 200:
            assert body['message'] == response['message']
        else:
            # 400 参数校验失败:错误信息在 errors 数组;业务失败:在顶层 message 字段
            if 'errors' in body:
                actual_message = body['errors'][0]['msg']
            else:
                actual_message = body['message']
            assert actual_message == response['message'], resp.text


class TestProfileFlow:
    """个人资料链路:注册 → 修改资料 → 查询确认(数据自清理)"""

    def test_profile_update_flow(self, auth, unique_email):
        resp = auth.register(
            {'name': '资料测试', 'email': unique_email, 'password': 'pass123456'})
        assert resp.status_code == 201, resp.text
        token = resp.json()['token']

        resp = auth.profile(
            {'name': '资料测试改', 'phone': '13900139000'}, token)
        assert resp.status_code == 200, resp.text

        resp = auth.me({'token': token})
        assert resp.status_code == 200, resp.text
        assert resp.json()['user']['name'] == '资料测试改'
        assert resp.json()['user']['phone'] == '13900139000'
