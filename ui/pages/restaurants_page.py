"""餐厅列表页 /restaurants"""
from playwright.sync_api import Page

from .base_page import BasePage


class RestaurantsPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def goto(self):
        self.page.goto('/restaurants')
        return self

    def search(self, keyword: str):
        """输入搜索关键词(前端有 500ms 防抖,断言侧等待结果)"""
        self.page.get_by_test_id('restaurants-search').fill(keyword)
        return self

    def filter_cuisine(self, cuisine: str):
        self.page.get_by_test_id(f'cuisine-{cuisine}').click()
        return self

    def card(self, restaurant_id):
        return self.page.get_by_test_id(f'restaurant-card-{restaurant_id}')
