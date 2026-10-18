"""登录/注册 UI 用例(P0):登录成功、密码错误提示、注册成功"""
from playwright.sync_api import expect

import config
from ui.pages.login_page import LoginPage
from ui.pages.register_page import RegisterPage


def test_login_success(guest_context, test_accounts):
    """正确凭据登录 → 跳转首页,头部显示用户名"""
    info = test_accounts['client']
    page = guest_context.new_page()
    LoginPage(page).goto().login(info['email'], info['password'])
    expect(page).to_have_url(f'{config.FRONTEND_URL}/')
    expect(page.get_by_test_id('header-user-menu')).to_contain_text(
        'Carlos Rodríguez')
    page.close()


def test_login_wrong_password(guest_context, test_accounts):
    """错误密码 → 页面停留登录页,toast 提示错误消息"""
    info = test_accounts['client']
    page = guest_context.new_page()
    LoginPage(page).goto().login(info['email'], 'wrong_password_123')
    expect(page.get_by_text('账号或密码错误')).to_be_visible()
    expect(page.get_by_test_id('login-submit')).to_be_visible()
    page.close()


def test_register_success(guest_context, unique_email):
    """注册成功 → 自动登录,头部显示新用户名"""
    page = guest_context.new_page()
    RegisterPage(page).goto().register('UI测试用户', unique_email, 'pass123456')
    expect(page).to_have_url(f'{config.FRONTEND_URL}/')
    expect(page.get_by_test_id('header-user-menu')).to_contain_text(
        'UI测试用户')
    page.close()
