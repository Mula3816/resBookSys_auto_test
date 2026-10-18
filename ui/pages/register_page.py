"""注册页 /auth/register"""
from playwright.sync_api import Page

from .base_page import BasePage


class RegisterPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def goto(self):
        self.page.goto('/auth/register')
        return self

    def register(self, name: str, email: str, password: str):
        """填写并提交注册表单(默认客户身份)"""
        self.page.get_by_test_id('register-name').fill(name)
        self.page.get_by_test_id('register-email').fill(email)
        self.page.get_by_test_id('register-password').fill(password)
        self.page.get_by_test_id('register-confirm-password').fill(password)
        self.page.get_by_test_id('register-submit').click()
        return self
