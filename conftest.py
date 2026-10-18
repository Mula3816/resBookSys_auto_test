"""pytest 公共 fixture

- backend_server: 会话级。检测被测后端是否已启动,未启动则自动拉起
  (node server.js),测试全部结束后再关闭;已启动的则保持原样。
- test_accounts:  加载 data/accounts.json 中的预置测试账号。
- unique_email:   生成不重复的邮箱,供注册类用例使用。
"""
import json
import os
import subprocess
import time
import uuid

import pytest
import requests

import config
from api.auth_api import AuthApi
from common.db_cleaner import clean_test_data

# xdist 并发模式下跳过会话级数据清理,避免各 worker 相互竞争
# (链路用例自身有自愈清理,注册用例用随机邮箱,残留由下次串行运行清理)
IS_XDIST_WORKER = 'PYTEST_XDIST_WORKER' in os.environ


def _health_ok() -> bool:
    try:
        resp = requests.get(f'{config.BASE_URL}{config.HEALTH_PATH}', timeout=2)
        return resp.status_code == 200
    except requests.RequestException:
        return False


def _wait_until_healthy(timeout: int = config.SERVER_START_TIMEOUT) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _health_ok():
            return True
        time.sleep(1)
    return False


@pytest.fixture(scope='session', autouse=True)
def db_cleanup():
    """会话开始前清残留(防止上次运行中断污染),结束后清测试数据。

    定义在 backend_server 之前并作为其依赖:保证清理发生在服务启动前/停止后。
    并发模式(xdist)下跳过,避免各 worker 相互竞争。
    """
    if not IS_XDIST_WORKER:
        clean_test_data()
    yield
    if not IS_XDIST_WORKER:
        clean_test_data()


@pytest.fixture(scope='session', autouse=True)
def backend_server(db_cleanup):
    """确保被测后端可用;自动拉起的服务在会话结束后关闭。

    串行模式:未启动则自动拉起、结束回收;
    并发模式(xdist):服务生命周期由运行器(CI / scripts/run_ci.sh)管理,
    这里只检查就绪——否则各 worker 会互相拉起/关闭服务。
    """
    if _health_ok():
        yield
        return

    if IS_XDIST_WORKER:
        pytest.fail('并发模式下后端未就绪:请先启动服务,'
                    '或使用 ./scripts/run_ci.sh -n auto 运行')

    log_file = open(config.SERVER_LOG, 'a', encoding='utf-8')
    proc = subprocess.Popen(
        ['node', 'server.js'],
        cwd=config.BACKEND_DIR,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )
    try:
        if not _wait_until_healthy():
            pytest.fail(
                f'后端服务 {config.SERVER_START_TIMEOUT}s 内未就绪'
                f'(地址: {config.BASE_URL}),请查看日志 {config.SERVER_LOG}')
        yield
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        log_file.close()


@pytest.fixture(scope='session')
def test_accounts() -> dict:
    """预置测试账号(种子数据,密码见 data/accounts.json)"""
    path = os.path.join(config.DATA_DIR, 'accounts.json')
    with open(path, encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def unique_email() -> str:
    """每次生成唯一邮箱,保证注册类用例可重复执行"""
    return f'auto_test_{uuid.uuid4().hex[:10]}@example.com'


@pytest.fixture
def unique_name() -> str:
    """每次生成唯一的测试餐厅名(auto_test_ 前缀,清理 fixture 据此识别)"""
    return f'auto_test_restaurant_{uuid.uuid4().hex[:8]}'


@pytest.fixture(scope='session')
def client_token(test_accounts) -> str:
    """登录 client 预置账号,返回有效 token(供 /me 类用例使用)"""
    return _login_token(test_accounts['client'])


@pytest.fixture(scope='session')
def merchant_token(test_accounts) -> str:
    """登录 merchant 预置账号,返回有效 token(供商家类用例使用)"""
    return _login_token(test_accounts['merchant'])


@pytest.fixture(scope='session')
def admin_token(test_accounts) -> str:
    """登录 admin 预置账号,返回有效 token(供用户管理类用例使用)"""
    return _login_token(test_accounts['admin'])


def _login_token(info: dict) -> str:
    resp = AuthApi().login(
        {'email': info['email'], 'password': info['password']})
    assert resp.status_code == 200, resp.text
    return resp.json()['token']
