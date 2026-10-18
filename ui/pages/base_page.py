"""页面对象基类:持有 page 引用,公共断言按需扩展"""
from playwright.sync_api import Page


class BasePage:
    def __init__(self, page: Page):
        self.page = page
