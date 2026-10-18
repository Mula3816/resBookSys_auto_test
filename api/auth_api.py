"""认证模块接口封装(与后端 routes/auth.js 对应)

- POST /api/auth/register  注册
- POST /api/auth/login     登录
- GET  /api/auth/me        当前用户(Bearer token 鉴权)
"""
from common.request_client import RequestClient
import config


class AuthApi:
    """餐厅订位系统认证模块接口"""

    PATH = config.AUTH_PATH  # /api/auth

    def __init__(self, client: RequestClient = None):
        self.client = client or RequestClient()

    '''
    def login(self, email: str, password: str):
            """登录"""
            return self.client.request(
                'POST', f'{self.PATH}/login',
                json={'email': email, 'password': password})
    '''
    
    def login(self, req_data: dict):
            """登录"""
            return self.client.request(
                'POST', f'{self.PATH}/login',
                json=req_data)

    '''
    def register(self, name: str, email: str, password: str,
                 phone: str = None, role: str = None):
        """注册(phone/role 为可选字段,None 时不发送)"""
        payload = {'name': name, 'email': email, 'password': password}
        if phone is not None:
            payload['phone'] = phone
        if role is not None:
            payload['role'] = role
        return self.client.request(
            'POST', f'{self.PATH}/register', json=payload)
    '''

    def register(self, req_data: dict):
        """注册"""
        return self.client.request(
            'POST', f'{self.PATH}/register', json=req_data)

    '''
    def me(self, token: str = None):
        """获取当前用户;token 为空时不携带 Authorization 头"""
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        return self.client.request('GET', f'{self.PATH}/me', headers=headers)
    '''

    def me(self, req_data: dict = None):
        """获取当前用户;req_data 含 token 时携带 Authorization 头"""
        req_data = req_data or {}
        token = req_data.get('token')
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        return self.client.request('GET', f'{self.PATH}/me', headers=headers)

    def profile(self, req_data: dict, token: str):
        """更新个人资料(name/phone)"""
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        return self.client.request(
            'PUT', f'{self.PATH}/profile', headers=headers, json=req_data)
