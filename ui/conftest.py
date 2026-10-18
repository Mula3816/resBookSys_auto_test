"""UI 自动化测试公共 fixture

复用根 conftest 的后端服务管理/数据清理/账号/token fixtures(importlib 加载),
新增:
- frontend_server: 自动拉起前端 dev 服务(3000 端口),结束回收
- guest/client/merchant/admin context: 按角色注入 sessionStorage token 的浏览器上下文
  (前端 AuthContext 从 sessionStorage 读 token,init script 在每次页面加载前注入,
   避免每个用例都走一遍 UI 登录,登录流程本身由专门的登录用例覆盖)
"""
import importlib.util
import os
import subprocess
import sys
import time

import pytest
import requests
from playwright.sync_api import expect

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import config  # noqa: E402

# 报告目录在全新环境(CI 检出)中不存在,提前创建
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'report'),
            exist_ok=True)

# 断言默认超时 10s(dev 服务下页面加载较慢)
expect.set_options(timeout=10_000)

# 复用根 conftest 的 fixtures
_root_conftest_path = os.path.join(PROJECT_ROOT, 'conftest.py')
_spec = importlib.util.spec_from_file_location(
    'root_conftest', _root_conftest_path)
_root_conftest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_root_conftest)

backend_server = _root_conftest.backend_server
db_cleanup = _root_conftest.db_cleanup
test_accounts = _root_conftest.test_accounts
client_token = _root_conftest.client_token
merchant_token = _root_conftest.merchant_token
admin_token = _root_conftest.admin_token
unique_email = _root_conftest.unique_email


def _frontend_ok() -> bool:
    try:
        return requests.get(f'{config.FRONTEND_URL}/', timeout=2).status_code == 200
    except requests.RequestException:
        return False


@pytest.fixture(scope='session', autouse=True)
def frontend_server():
    """确保前端 dev 服务可用;未启动则自动拉起(react-scripts 首次编译较慢)"""
    if _frontend_ok():
        yield
        return

    os.makedirs(os.path.dirname(config.UI_SERVER_LOG), exist_ok=True)
    log_file = open(config.UI_SERVER_LOG, 'a', encoding='utf-8')
    proc = subprocess.Popen(
        ['npm', 'start'],
        cwd=config.FRONTEND_DIR,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        env={**os.environ, 'BROWSER': 'none', 'CI': 'false'},
        # BROWSER=none 阻止自动打开浏览器;CI=false 规避 react-scripts 的 CI 行为差异
    )
    try:
        deadline = time.time() + 150  # 首次编译 30~60s,留足余量
        while time.time() < deadline:
            if _frontend_ok():
                break
            time.sleep(2)
        else:
            pytest.fail(f'前端服务 150s 内未就绪,日志: {config.UI_SERVER_LOG}')
        yield
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        log_file.close()


def _make_context(browser, token: str = None):
    """创建浏览器上下文;token 非空时通过 init script 注入 sessionStorage"""
    context = browser.new_context(base_url=config.FRONTEND_URL)
    if token:
        context.add_init_script(
            f"window.sessionStorage.setItem('token', '{token}');")
    return context


@pytest.fixture
def guest_context(browser):
    """游客上下文(无登录态)"""
    context = _make_context(browser)
    yield context
    context.close()


@pytest.fixture
def client_context(browser, client_token):
    """客户登录态上下文(token 由 API 登录获得,注入 sessionStorage)"""
    context = _make_context(browser, client_token)
    yield context
    context.close()


@pytest.fixture
def merchant_context(browser, merchant_token):
    """商家登录态上下文"""
    context = _make_context(browser, merchant_token)
    yield context
    context.close()


@pytest.fixture
def admin_context(browser, admin_token):
    """管理员登录态上下文"""
    context = _make_context(browser, admin_token)
    yield context
    context.close()
