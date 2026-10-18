"""游客浏览链路(P0):首页 → 餐厅列表/筛选/搜索 → 餐厅详情"""
from playwright.sync_api import expect

import config
from ui.pages.restaurant_detail_page import RestaurantDetailPage
from ui.pages.restaurants_page import RestaurantsPage


def test_home_page_guest(guest_context):
    page = guest_context.new_page()
    page.goto('/')
    expect(page.get_by_role('heading', name='预订顶级餐厅')).to_be_visible()
    expect(page.get_by_test_id('header-login')).to_be_visible()
    expect(page.get_by_test_id('header-register')).to_be_visible()
    page.close()


def test_restaurants_list_filter_search(guest_context):
    """列表展示 → 菜系筛选(可切换)→ 搜索(前端有 500ms 防抖,断言自动等待)

    注意:搜索词与菜系筛选是叠加关系,本用例分开验证。
    """
    page = guest_context.new_page()
    restaurants = RestaurantsPage(page).goto()

    # 默认列表包含种子餐厅
    expect(restaurants.card(1)).to_be_visible()  # La Mar(秘鲁菜)
    expect(restaurants.card(7)).to_be_visible()  # Great Wall Chinese(中餐)

    # 菜系筛选"中餐" → 只剩中餐厅
    restaurants.filter_cuisine('中餐')
    expect(restaurants.card(7)).to_be_visible()
    expect(restaurants.card(1)).to_have_count(0)

    # 再次点击取消筛选 → 恢复全部
    restaurants.filter_cuisine('中餐')
    expect(restaurants.card(1)).to_be_visible()
    expect(restaurants.card(7)).to_be_visible()

    # 搜索 La Mar(防抖后生效,无筛选)
    restaurants.search('La Mar')
    expect(restaurants.card(1)).to_be_visible()
    expect(restaurants.card(7)).to_have_count(0)
    page.close()


def test_restaurant_detail_guest(guest_context):
    """游客查看餐厅详情:信息、桌台;查询可订时段后按钮显示「登录后预订」

    注:预订按钮仅在查询可订时段后渲染,游客状态显示"登录后预订"。
    """
    page = guest_context.new_page()
    detail = RestaurantDetailPage(page).goto(1)
    expect(page.get_by_role('heading', name='La Mar')).to_be_visible()
    expect(page.get_by_text('米拉弗洛雷斯区拉玛尔大道 123 号')).to_be_visible()
    expect(page.get_by_text('桌台 1-1', exact=True)).to_be_visible()

    detail.select_date(config.UI_BOOKING_DATE).check_availability()
    try:
        expect(page.get_by_text('可订时段')).to_be_visible()
    except AssertionError:
        # 诊断:查询失败时页面会出现错误 toast,带上它便于定位
        toasts = page.locator('[role="status"]').all_inner_texts()
        raise AssertionError(f'可订时段未出现,页面 toast 内容: {toasts}') from None
    expect(page.get_by_test_id('detail-continue-booking')).to_contain_text(
        '登录后预订')
    page.close()
