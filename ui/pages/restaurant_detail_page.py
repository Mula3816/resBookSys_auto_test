"""餐厅详情页 /restaurants/:id"""
from playwright.sync_api import Page

from .base_page import BasePage


class RestaurantDetailPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def goto(self, restaurant_id: int):
        self.page.goto(f'/restaurants/{restaurant_id}')
        return self

    def select_date(self, date: str):
        self.page.get_by_test_id('detail-date').fill(date)
        return self

    def select_party_size(self, size: int):
        self.page.get_by_test_id('detail-party-size').select_option(str(size))
        return self

    def check_availability(self):
        self.page.get_by_test_id('detail-check-availability').click()
        return self

    def continue_booking(self):
        self.page.get_by_test_id('detail-continue-booking').click()
        return self
