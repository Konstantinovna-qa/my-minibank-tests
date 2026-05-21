import pytest

from config.settings import settings, UserRole
from ui.pages.login_page import LoginPage
from ui.pages.accounts_page import AccountsPage
from ui.pages.dashboard_page import DashboardPage
import structlog

logger = structlog.get_logger(__name__)

@pytest.mark.ui
@pytest.mark.accounts
class TestUIAccountCreation:
    def test_view_user_accounts(self, driver):
        """Пользователь USER может открыть страницу счетов и увидеть хотя бы один счет"""

        login_page = LoginPage(driver)
        login_page.navigate_to()
        login_page.assert_page_loaded()

        test_user = settings.get_user(UserRole.USER)
        login_page.login(test_user.email, test_user.password)

        dashboard_page = DashboardPage(driver)
        dashboard_page.open_accounts()

        accounts_page = AccountsPage(driver)
        accounts_page.wait_until_loaded()  # Ждем, пока страница счетов загрузится

        assert accounts_page.is_loaded(), "The invoices page did not load"  # Проверяем, что страница действительно загружена

        account_cards = accounts_page.get_account_cards()  # Получаем список карточек счетов
        assert len(account_cards) > 0, "The user has no accounts."  # Проверяем, что есть хотя бы один счет

        first_account = account_cards[0]  # Извлекаем информацию о первом счете
        logger.info(f"First account details: {first_account}")  # Выводим информацию первого счета



    def test_user_account_permissions(self, driver):
        """Тест прав USER"""

        login_page = LoginPage(driver)
        login_page.navigate_to()
        login_page.assert_page_loaded()


        test_user = settings.get_user(UserRole.USER)
        login_page.login(test_user.email, test_user.password)

        dashboard_page = DashboardPage(driver)
        dashboard_page.open_accounts()

        accounts_page = AccountsPage(driver)
        accounts_page.wait_until_loaded()
        assert accounts_page.is_loaded(), "Accounts page not loaded"


        assert accounts_page.is_element_visible(  # Проверяем, что кнопка создания счета отображается
            accounts_page.selectors["create_button"]), "Create account button is not visible"

        account_cards = accounts_page.get_account_cards()
        assert len(account_cards) > 0, "У USER нет счетов"

        accounts_page.open_create_form()

        assert not accounts_page.is_element_immediately_visible(accounts_page.selectors["user_select"]), "USER не должен видеть поле выбора пользователя"
        assert not accounts_page.is_element_immediately_visible(accounts_page.selectors["initial_balance_input"]), "USER не должен видеть поле начального баланса"



    def test_admin_account_permissions(self, driver):
        """Тест прав ADMIN"""

        login_page = LoginPage(driver)
        login_page.navigate_to()
        login_page.assert_page_loaded()

        test_user = settings.get_user(UserRole.ADMIN)
        login_page.login(test_user.email, test_user.password)

        dashboard_page = DashboardPage(driver)
        dashboard_page.open_accounts()

        accounts_page = AccountsPage(driver)
        accounts_page.wait_until_loaded()
        assert accounts_page.is_loaded(), "Accounts page not loaded"

        assert accounts_page.is_element_visible(  # Проверяем, что кнопка создания счета отображается
            accounts_page.selectors["create_button"]), "Create account button is not visible"

        accounts_page.open_create_form()  # Открываем форму создания

        assert accounts_page.is_element_visible(  # Проверяем,что поле поле для выбора пользователя отображается
            accounts_page.selectors["user_select"]), "The user selection field is not displayed."
        assert accounts_page.is_element_visible(  # Проверяем, что поле для установки начального баланса отображается
            accounts_page.selectors["initial_balance_input"]), "The field for setting the initial balance is not visible."

        accounts_page.cancel_create()  # Закрываем форму без создания счета



    def test_create_basic_account(self,api_client, driver):
        """Тест создания счета с ролью ADMIN"""

        # API ТЕСТ
        login_response = api_client.login_as_role(UserRole.ADMIN)  # Логинимся как ADMIN через API
        assert login_response.success, f"API Admin login failed: {login_response.message}"

        users_response = api_client.get_users()  # Получаем список пользователей
        assert users_response.success, f"Failed to get users: {users_response.message}"

        settings_user = settings.get_user(UserRole.USER)  # Извлекаем UUID нужного пользователя
        user_uuid = None
        if users_response.data and 'users' in users_response.data:
            for user in users_response.data['users']:
                if user['email'] == settings_user.email:
                    user_uuid = user['id']
        assert user_uuid is not None, f"User with email {settings_user.email} was not found"

        # UI ТЕСТ
        login_page = LoginPage(driver)  # Создаем объект страницы входа
        login_page.navigate_to()  # Открываем страницу входа в браузере
        login_page.assert_page_loaded()  # Проверяем, что страница входа успешно загрузилась

        test_user = settings.get_user(UserRole.ADMIN)
        login_page.login(test_user.email, test_user.password)

        dashboard_page = DashboardPage(driver)  # Создаем объект главной страницы
        dashboard_page.open_accounts()  # Кликаем на кнопку для перехода к счетам

        accounts_page = AccountsPage(driver)  # Создаем объект страницы счетов
        accounts_page.wait_until_loaded()  # Ждем, пока страница счетов загрузится
        assert accounts_page.is_loaded(), "The accounts page did not load "  # Проверяем, что страница действительно загружена

        account_cards_before = accounts_page.get_account_cards()
        count_before = len(account_cards_before)

        accounts_page.create_account(
            account_type="CHECKING",
            initial_balance=100.0,
            user_id=user_uuid
        )
        accounts_page.wait_for_loading_to_complete()

        account_cards_after = accounts_page.get_account_cards()
        count_after = len(account_cards_after)

        assert count_after == count_before + 1, (
            f"Количество счетов не увеличилось. Было: {count_before}, стало: {count_after}"
        )

        accounts_page.refresh_page()   # Обновляем страницу, чтобы увидеть новый счет
        accounts_page.wait_until_loaded()  # Ждем загрузки после обновления

        assert not accounts_page.is_element_visible(accounts_page.selectors["no_accounts"]), "No accounts message is displayed, but accounts should exist"  # Проверяем, что счет создался
