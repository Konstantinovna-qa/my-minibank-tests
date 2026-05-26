import pytest

from config.settings import settings, UserRole
from ui.pages.login_page import LoginPage
from ui.pages.dashboard_page import DashboardPage
from ui.pages.users_page import UsersPage
import utils.helpers as helpers
import structlog

logger = structlog.get_logger(__name__)


@pytest.mark.ui
@pytest.mark.users
class TestUIManagement:

    def test_admin_can_view_users(self, driver):
        """Просмотр страницы пользователей (Users) в роли ADMIN"""

        login_page = LoginPage(driver)
        login_page.navigate_to()
        login_page.assert_page_loaded()

        test_user = settings.get_user(UserRole.ADMIN)
        login_page.login(test_user.email, test_user.password)

        dashboard_page = DashboardPage(driver)
        dashboard_page.assert_page_loaded()
        dashboard_page.open_users()

        users_page = UsersPage(driver)
        users_page.wait_until_loaded()

        assert users_page.is_loaded(), "Users page not loaded"

        count = users_page.get_users_count()  # Получаем количество пользователей на странице Users
        logger.info("Users count", count=count)  # Записываем количество найденных пользователей в лог

        assert count > 0, "No users found in users list"  # Проверяем, что в списке пользователей есть хотя бы один пользователь



    def test_create_basic_user(self, driver):
        """Тест создания пользователя с ролью USER через ADMIN"""

        login_page = LoginPage(driver)  # Открываем страницу логина
        login_page.navigate_to()
        login_page.assert_page_loaded()  # Проверяем, что страница логина загрузилась

        test_user = settings.get_user(UserRole.ADMIN)
        login_page.login(test_user.email, test_user.password)  # Логинимся под ADMIN

        dashboard_page = DashboardPage(driver)   # Открываем Dashboard
        dashboard_page.assert_page_loaded()

        dashboard_page.open_users()  # Переходим на страницу Users
        users_page = UsersPage(driver)  # Открываем страницу пользователей
        users_page.wait_until_loaded()

        assert users_page.is_loaded(), "Users page not loaded"  # Проверяем, что страница Users загрузилась

        assert users_page.is_element_visible(
            users_page.selectors["create_user_button"]), "Create user button is not visible"  # Проверяем, что кнопка создания пользователя отображается

        users_page.open_create_user_form()  # Открываем форму создания пользователя
        user_data = helpers.create_unique_user_data()  # Создаем уникальные тестовые данные пользователя
        user_data["password"] = "password123"
        users_page.create_user(user_data, role="USER")  # Создаем пользователя с ролью USER

        assert users_page.is_user_visible(user_data["email"]), "Created user is not displayed in users list"  # Пользователь появился в списке по email

        assert users_page.is_user_name_correct(  # Проверяем отображение данных пользователя
            user_data["email"],
            user_data["firstName"],
            user_data["lastName"]
        ), "User name is incorrect"

        assert users_page.is_user_role_correct(
            user_data["email"],
            "USER"
        ), "User role is incorrect"



    def test_user_cannot_manage_users(self, driver):
        """USER не должен иметь доступ к Users"""

        login_page = LoginPage(driver)  # Открываем страницу логина
        login_page.navigate_to()
        login_page.assert_page_loaded()  # Проверяем, что страница логина загрузилась

        test_user = settings.get_user(UserRole.USER)
        login_page.login(test_user.email, test_user.password)  # Логинимся под USER

        dashboard_page = DashboardPage(driver)
        dashboard_page.assert_page_loaded()

        assert not dashboard_page.is_element_visible(  # Проверяем что кнопки Users нет
            "//button[contains(text(), 'Users')]"
        ), "Users button should not be visible for USER role"

        driver.get(f"{settings.base_url}/users")  # Пробуем перейти по прямой ссылке


        assert "Authentication required" in driver.page_source, "USER should not have access to Users page"
