"""管理后台冒烟(P0):管理员/商家均可打开管理仪表盘"""
from playwright.sync_api import expect


def test_admin_dashboard(admin_context):
    page = admin_context.new_page()
    page.goto('/admin')
    expect(page.get_by_role('heading', name='管理仪表盘')).to_be_visible()
    page.close()


def test_merchant_dashboard(merchant_context):
    page = merchant_context.new_page()
    page.goto('/admin')
    expect(page.get_by_role('heading', name='管理仪表盘')).to_be_visible()
    page.close()
