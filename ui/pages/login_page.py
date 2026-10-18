"""登录页 /auth/login"""
from playwright.sync_api import Page

from .base_page import BasePage


class LoginPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

    def goto(self):
        self.page.goto('/auth/login')
        return self

    def login(self, email: str, password: str):
        """填写并提交登录表单"""
        self.page.get_by_test_id('login-email').fill(email)
        self.page.get_by_test_id('login-password').fill(password)
        self.page.get_by_test_id('login-submit').click()
        return self
