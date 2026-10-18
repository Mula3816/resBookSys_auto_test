"""预订页 /booking/:restaurantId(依赖详情页 navigate 传入的 state)"""
from playwright.sync_api import Page

from .base_page import BasePage


class BookingPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def select_time(self, time: str):
        """选择用餐时段(如 '11:00')"""
        self.page.get_by_test_id(f'booking-slot-{time}').click()
        return self

    def select_occasion(self, occasion: str):
        self.page.get_by_test_id('booking-occasion').select_option(occasion)
        return self

    def submit(self):
        self.page.get_by_test_id('booking-submit').click()
        return self
