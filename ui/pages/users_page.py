"""
Страница пользователей для автотестов MiniBank
Обрабатывает действия по управлению пользователями
"""

from typing import List, Dict, Any
import structlog

from .base_page import BasePage

logger = structlog.get_logger(__name__)


class UsersPage(BasePage):
    """Страница управления пользователями"""

    def __init__(self, driver):
        super().__init__(driver)
        self.selectors.update({
            "users_title": "//h1[text()='User Management']",
            "create_user_button": "//button[contains(text(), 'Create User')]",

            "name_column": "//div[text()='Name']",
            "email_column": "//div[text()='Email']",
            "role_column": "//div[text()='Role']",

            "user_row": "//div[.//button[text()='Edit']]",
            "password_input": "//input[@name='password']",
            "create_user_form": "//h2[contains(text(), 'Create') or contains(text(), 'User')]",
            "first_name_input": "//input[@name='firstName']",
            "last_name_input": "//input[@name='lastName']",
            "email_input": "//input[@name='email']",
            "role_select": "//select[@name='role']",
            "submit_create": "//button[@type='submit' and contains(text(), 'Create User')]",
            "success_message": "//*[contains(text(), 'success') or contains(text(), 'created') or contains(text(), 'Created')]",
            "error_message": "//*[contains(text(), 'error') or contains(text(), 'Error')]",
            "no_users_message": "//*[contains(text(), 'No users') or contains(text(), 'No Users')]",
        })

    # --------------------------------------------------------------------
    # Реализация абстрактных методов
    # --------------------------------------------------------------------

    def wait_until_loaded(self) -> None:
        """Ожидает полной загрузки страницы пользователей"""
        self.wait_for_element(self.selectors["users_title"])
        self.wait_for_element(self.selectors["create_user_button"])


    def is_loaded(self) -> bool:
        """Проверяет, что страница пользователей загружена"""
        return (
            self.is_element_immediately_visible(self.selectors["users_title"])
            and self.is_element_immediately_visible(self.selectors["create_user_button"])
            and self.is_element_immediately_visible(self.selectors["name_column"])
        )

    def get_page_title(self) -> str:
        """Возвращает название страницы"""
        return "User Management"

    # --------------------------------------------------------------------
    # Действия на странице
    # --------------------------------------------------------------------

    def open_create_user_form(self) -> None:
        """Открывает форму создания пользователя"""
        self.click_element(self.selectors["create_user_button"])
        self.wait_for_element(self.selectors["first_name_input"])

    def create_user(self, user_data: Dict[str, Any], role: str = "USER") -> None:
        """Создает нового пользователя"""

        self.fill_input(self.selectors["first_name_input"], user_data["firstName"])
        self.fill_input(self.selectors["last_name_input"], user_data["lastName"])
        self.fill_input(self.selectors["email_input"], user_data["email"])
        self.fill_input(self.selectors["password_input"],user_data["password"])

        if self.is_element_visible(self.selectors["role_select"], timeout=1):
            self.select_option(self.selectors["role_select"], role)

        self.click_element(self.selectors["submit_create"])
        self.wait_for_loading_to_complete()

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

    def is_user_visible(self, email: str) -> bool:
        """Проверяет, что пользователь отображается в списке по email"""
        user_email_locator = f"//div[contains(text(), '{email}')]"
        return self.is_element_visible(user_email_locator)

    def get_user_row(self, email: str):
        """Возвращает строку пользователя по email"""
        user_locator = f"//div[contains(text(), '{email}')]/ancestor::div[.//button[text()='Edit']]"
        return self.find_element(user_locator)

    def show_user_details(self, user_id: str) -> None:
        """Открывает детали пользователя"""
        details_selector = f'[data-testid="details-button-{user_id}"]'
        self.click_element(details_selector)
        self.wait_for_loading_to_complete()

    def is_user_name_correct(
            self,
            email: str,
            first_name: str,
            last_name: str
    ) -> bool:
        """Проверяет имя и фамилию пользователя по email"""
        user_locator = (
            f"//div[contains(text(), '{email}')]/ancestor::div[.//button[text()='Edit']]"
        )
        user_row = self.find_element(user_locator)
        return (
                first_name in user_row.text
                and last_name in user_row.text
        )

    def delete_user(self, user_id: str) -> None:
        """Удаляет пользователя"""
        delete_selector = f'[data-testid="delete-button-{user_id}"]'
        self.click_element(delete_selector)
        self.handle_alert(True)
        self.wait_for_loading_to_complete()

    # --------------------------------------------------------------------
    # Проверки состояния
    # --------------------------------------------------------------------

    def is_success_message_visible(self) -> bool:
        """Проверяет сообщение об успешном создании пользователя"""
        return self.is_element_visible(self.selectors["success_message"])

    def assert_user_exists(self, email: str) -> None:
        """Проверяет существование пользователя по email"""
        assert self.is_user_visible(email), f"User with email {email} not found"

    def is_user_role_correct(self, email: str, role: str) -> bool:
        """Проверяет роль пользователя"""
        user_row = self.get_user_row(email)
        return role in user_row.text

    def assert_no_users(self) -> None:
        """Проверяет сообщение об отсутствии пользователей"""
        assert self.is_element_visible(
            self.selectors["no_users_message"]
        ), "Expected no users message"

    def assert_error_message(self, message: str = None) -> None:
        """Проверяет отображение ошибки"""
        assert self.is_element_visible(
            self.selectors["error_message"]
        ), "Error message not visible"

        if message:
            error_text = self.get_text(self.selectors["error_message"])

            assert message in error_text, (
                f"Expected '{message}' in error text '{error_text}'"
            )
