"""预订核心链路(P0):详情页订位 → 我的预订 → 取消

- 登录态由 API 登录后注入 sessionStorage(不重复测登录)
- 数据准备/清理走 API 层,UI 只验证"页面真实走通"
"""
from playwright.sync_api import expect

import config
from api.reservations_api import ReservationsApi
from ui.pages.booking_page import BookingPage
from ui.pages.restaurant_detail_page import RestaurantDetailPage


def _cancel_ui_reservations(client_token):
    """清理 UI 用例产生的预订(失败重试时保证可重复执行)"""
    api = ReservationsApi()
    resp = api.list(client_token, date_from=config.UI_BOOKING_DATE,
                    date_to=config.UI_BOOKING_DATE)
    for r in resp.json()['reservations']:
        api.cancel(r['id'], {'reason': 'UI 用例清理'}, client_token)


def test_booking_flow(client_context, client_token):
    """选日期 → 查可订时段 → 选时段提交 → 成功 toast → 我的预订可见"""
    page = client_context.new_page()
    detail = RestaurantDetailPage(page).goto(1)
    expect(page.get_by_role('heading', name='La Mar')).to_be_visible()

    detail.select_date(config.UI_BOOKING_DATE).check_availability()
    expect(page.get_by_text('可订时段')).to_be_visible()
    detail.continue_booking()

    booking = BookingPage(page)
    booking.select_time('11:00')
    booking.select_occasion('生日')
    booking.submit()

    # 成功提示 + 跳转"我的预订",列表出现 La Mar
    expect(page.get_by_text('预订已确认！确认码：')).to_be_visible()
    expect(page.get_by_role('heading', name='我的预订')).to_be_visible()
    expect(page.get_by_text('La Mar').first).to_be_visible()
    page.close()

    _cancel_ui_reservations(client_token)


def test_my_reservations_and_cancel(client_context, client_token):
    """API 造数 → UI 展示预订 → 取消交互(prompt 自动接受)→ 取消按钮消失"""
    api = ReservationsApi()
    resp = api.create({
        'restaurant_id': 1, 'table_id': 2,
        'reservation_date': config.UI_BOOKING_DATE, 'reservation_time': '20:00',
        'party_size': 2
    }, client_token)
    assert resp.status_code == 201, resp.text
    reservation_id = resp.json()['reservationId']

    page = client_context.new_page()
    page.goto('/reservations')
    # 列表可能含其他用例留下的 La Mar 预订(已取消),取第一个即可
    expect(page.get_by_text('La Mar').first).to_be_visible()

    # 前端取消使用 window.prompt,注册对话框处理器自动接受
    page.on('dialog', lambda dialog: dialog.accept('UI 用例取消'))
    cancel_button = page.get_by_test_id(
        f'reservation-cancel-{reservation_id}')
    expect(cancel_button).to_be_visible()
    cancel_button.click()

    expect(page.get_by_text('预订已成功取消')).to_be_visible()
    expect(page.get_by_test_id(
        f'reservation-cancel-{reservation_id}')).to_have_count(0)
    page.close()
