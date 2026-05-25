

"""
Страница пользователей для автотестов MiniBank
Обрабатывает действия по управлению пользователями
"""

from selenium import webdriver
from typing import List
import structlog

from .base_page import BasePage

logger = structlog.get_logger(__name__)


class UsersPage(BasePage):
    """Страница управления пользователями"""

    def __init__(self, driver):
        super().__init__(driver)
        self.selectors = {
            "users_title": "//h1[text()='User Management']",
            "create_user_button": "//button[contains(text(), 'Create User')]",
            "name_column": "//div[text()='Name']",
            "email_column": "//div[text()='Email']",
            "user_row": "//div[.//button[text()='Edit']]",
            "role_column": "//div[text()='Role']",
        }

    def wait_until_loaded(self):
        """Ждём загрузку страницы Users"""
        self.wait_for_element(self.selectors["users_title"])
        self.wait_for_element(self.selectors["create_user_button"])
        self.wait_for_element(self.selectors["name_column"])

    def is_loaded(self):
        """Проверяем, что страница Users загрузилась"""
        return (
            self.is_element_visible(self.selectors["users_title"])
            and self.is_element_visible(self.selectors["create_user_button"])
            and self.is_element_visible(self.selectors["name_column"])
        )

    def get_page_title(self):
        return "User Management"


    # --------------------------------------------------------------------
    # Реализация абстрактных методов
    # --------------------------------------------------------------------

    def is_loaded(self) -> bool:
        """Проверяет загружена ли страница пользователей"""
        return self.is_element_immediately_visible(
            self.selectors["users_title"]
        )

    def wait_until_loaded(self) -> None:
        """Ожидает полной загрузки страницы пользователей"""
        self.wait_for_element(self.selectors["users_title"])

    def get_page_title(self) -> str:
        return "Users"

    # --------------------------------------------------------------------
    # Действия на странице
    # --------------------------------------------------------------------

    def open_create_user_form(self):
        """Открывает форму создания пользователя"""
        self.click_element(self.selectors["create_user_button"])
        self.wait_for_element(self.selectors["create_user_form"])

    def get_users(self) -> List[str]:
        """Получает список пользователей"""
        users = self.find_elements(self.selectors["user_row"])
        return [user.text for user in users]

    def get_users_count(self) -> int:
        """Возвращает количество пользователей"""

        users = self.find_elements(self.selectors["user_row"])
        count = len(users)

        self.logger.info(f"Users count: {count}")
        return count

    def show_user_details(self, user_id: str):
        """Открывает детали пользователя"""
        details_selector = f'[data-testid="details-button-{user_id}"]'
        self.click_element(details_selector)
        self.wait_for_loading_to_complete()

    def delete_user(self, user_id: str):
        """Удаляет пользователя"""
        delete_selector = f'[data-testid="delete-button-{user_id}"]'
        self.click_element(delete_selector)
        self.handle_alert(True)
        self.wait_for_loading_to_complete()

    # --------------------------------------------------------------------
    # Проверки состояния
    # --------------------------------------------------------------------

    def assert_user_exists(self, user_id: str):
        """Проверяет существование пользователя"""
        user_selector = f'[data-testid="user-row-{user_id}"]'

        assert self.is_element_visible(
            user_selector
        ), f"User {user_id} not found"

    def assert_no_users(self):
        """Проверяет сообщение об отсутствии пользователей"""

        assert self.is_element_visible(
            self.selectors["no_users_message"]
        ), "Expected no users message"

    def assert_error_message(self, message: str = None):
        """Проверяет отображение ошибки"""

        assert self.is_element_visible(
            self.selectors["error_message"]
        ), "Error message not visible"

        if message:
            error_text = self.get_text(
                self.selectors["error_message"]
            )

            assert message in error_text, (
                f"Expected '{message}' in error text '{error_text}'"
            )

