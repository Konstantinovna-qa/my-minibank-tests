from decimal import Decimal

import pytest
import structlog

from ui.pages.dashboard_page import DashboardPage
from ui.pages.login_page import LoginPage
from ui.pages.transfers_page import TransfersPage


logger = structlog.get_logger(__name__)


@pytest.mark.ui
@pytest.mark.transfers
class TestUITransfers:

    def test_transfer_form_elements(self, driver, api_client, user_with_two_accounts):
        """Проверка основных элементов формы перевода и количества доступных счетов"""

        test_data = user_with_two_accounts
        credentials = test_data["credentials"]

        login_page = LoginPage(driver)  # Вход через UI
        login_page.navigate_to()
        login_page.assert_page_loaded()
        login_page.login(
            credentials["email"],
            credentials["password"]
        )

        dashboard_page = DashboardPage(driver)  # Переходим на страницу переводов
        dashboard_page.assert_page_loaded()
        dashboard_page.open_transfers()

        transfers_page = TransfersPage(driver)  # Проверяем загрузку страницы переводов
        transfers_page.assert_page_loaded()

        transfers_page.assert_transfer_form_elements_visible()  # Проверяем наличие основных элементов формы

        available_accounts_count = (transfers_page.get_available_from_accounts_count())  # Получаем количество доступных счетов

        logger.info("Количество доступных счетов", accounts_count=available_accounts_count)  # Выводим количество счетов в логи

        assert available_accounts_count > 0, "Нет доступных счетов для перевода"  # Проверяем, что для перевода доступен хотя бы один счет

    def test_simple_transfer_between_accounts(self, driver, api_client, user_with_two_accounts):
        """Проверка успешного перевода между счетами пользователя через UI"""

        source_account = user_with_two_accounts["source_account"]
        target_account = user_with_two_accounts["target_account"]
        credentials = user_with_two_accounts["credentials"]

        amount = Decimal("50")

        api_login = api_client.login(  # Логинимся через API, чтобы получить актуальные балансы
            credentials["email"],
            credentials["password"]
        )

        assert api_login.success, f"API login failed: {api_login.message}"

        source_balance_response = api_client.get_account_balance(source_account["id"])  # Получаем актуальный баланс исходного счета

        assert source_balance_response.success, f"Failed to get source account balance: " f"{source_balance_response.message}"

        source_balance = Decimal(str(source_balance_response.data["account"]["balance"]))

        target_balance_response = api_client.get_account_balance(target_account["id"])  # Получаем актуальный баланс целевого счета

        assert target_balance_response.success, f"Failed to get target account balance: "f"{target_balance_response.message}"

        target_balance = Decimal(str(target_balance_response.data["account"]["balance"]))

        login_page = LoginPage(driver) # Логинимся через UI
        login_page.navigate_to()
        login_page.assert_page_loaded()

        login_page.login(
            credentials["email"],
            credentials["password"]
        )

        dashboard_page = DashboardPage(driver)  # Открываем страницу переводов
        dashboard_page.assert_page_loaded()
        dashboard_page.open_transfers()

        transfers_page = TransfersPage(driver)  # Выполняем перевод через UI
        transfers_page.wait_until_loaded()

        transfers_page.create_internal_transfer(
            str(source_account["id"]),
            str(target_account["id"]),
            amount
        )

        transfers_page.assert_success_message()  # Проверяем сообщение об успешном переводе

        accounts_response = api_client.get_accounts()  # Получаем обновленные счета через API

        assert accounts_response.success, f"Failed to get updated accounts: "f"{accounts_response.message}"

        accounts = accounts_response.data["accounts"]

        updated_source = next(acc for acc in accounts if acc["id"] == source_account["id"])

        updated_target = next(acc for acc in accounts if acc["id"] == target_account["id"])

        assert Decimal(str(updated_source["balance"])) == (source_balance - amount)  # Проверяем, что деньги списались с исходного счета

        assert Decimal(str(updated_target["balance"])) == (target_balance + amount)   # Проверяем, что деньги зачислились на целевой счет

    def test_transfer_insufficient_funds(self, driver, api_client, user_with_two_accounts):
        """Проверка ошибки перевода через UI при недостаточном балансе"""

        source_account = user_with_two_accounts["source_account"]
        target_account = user_with_two_accounts["target_account"]
        credentials = user_with_two_accounts["credentials"]

        amount = Decimal("100")

        api_login = api_client.login(  # Логинимся через API, чтобы получить актуальные балансы
            credentials["email"],
            credentials["password"]
        )

        assert api_login.success, f"API login failed: {api_login.message}"

        target_balance_response = api_client.get_account_balance(target_account["id"])  # Получаем баланс счета с деньгами

        assert target_balance_response.success, f"Failed to get target account balance: "f"{target_balance_response.message}"

        target_balance = Decimal(str(target_balance_response.data["account"]["balance"]))

        source_balance_response = api_client.get_account_balance(source_account["id"])  # Получаем баланс пустого счета

        assert source_balance_response.success, f"Failed to get source account balance: "f"{source_balance_response.message}"

        source_balance = Decimal(str(source_balance_response.data["account"]["balance"]))

        login_page = LoginPage(driver)  # Логинимся через UI
        login_page.navigate_to()
        login_page.assert_page_loaded()

        login_page.login(
            credentials["email"],
            credentials["password"]
        )

        dashboard_page = DashboardPage(driver)   # Открываем страницу переводов
        dashboard_page.assert_page_loaded()
        dashboard_page.open_transfers()

        transfers_page = TransfersPage(driver)  # Пытаемся выполнить перевод со счета без денег
        transfers_page.wait_until_loaded()

        transfers_page.create_internal_transfer(
            str(target_account["id"]),
            str(source_account["id"]),
            amount
        )

        transfers_page.assert_error_message()  # Проверяем отображение ошибки

        accounts_response = api_client.get_accounts()  # Получаем обновленные счета через API

        assert accounts_response.success, f"Failed to get updated accounts: "f"{accounts_response.message}"

        accounts = accounts_response.data["accounts"]

        updated_source = next(acc for acc in accounts if acc["id"] == source_account["id"])

        updated_target = next(acc for acc in accounts if acc["id"] == target_account["id"])

        assert Decimal(str(updated_source["balance"])) == source_balance  # Проверяем, что баланс исходного счета не изменился

        assert Decimal(str(updated_target["balance"])) == target_balance  # Проверяем, что баланс целевого счета не изменился

    def test_transfer_with_zero_amount_should_fail(self, driver, api_client, user_with_two_accounts):
        """Проверка ошибки перевода при вводе нулевой суммы"""

        source_account = user_with_two_accounts["source_account"]
        target_account = user_with_two_accounts["target_account"]
        credentials = user_with_two_accounts["credentials"]

        amount = Decimal("0")

        api_login = api_client.login(  # Логинимся через API, чтобы получить актуальные балансы
            credentials["email"],
            credentials["password"]
        )

        assert api_login.success, f"API login failed: {api_login.message}"

        target_balance_response = api_client.get_account_balance(target_account["id"])  # Получаем актуальный баланс целевого счета

        assert target_balance_response.success, f"Failed to get target account balance: "f"{target_balance_response.message}"

        target_balance = Decimal(str(target_balance_response.data["account"]["balance"]))

        source_balance_response = api_client.get_account_balance(source_account["id"])  # Получаем актуальный баланс исходного счета

        assert source_balance_response.success, f"Failed to get source account balance: "f"{source_balance_response.message}"

        source_balance = Decimal(str(source_balance_response.data["account"]["balance"]))

        login_page = LoginPage(driver)  # Логинимся через UI
        login_page.navigate_to()
        login_page.assert_page_loaded()

        login_page.login(
            credentials["email"],
            credentials["password"]
        )

        dashboard_page = DashboardPage(driver)  # Открываем страницу переводов
        dashboard_page.assert_page_loaded()
        dashboard_page.open_transfers()

        transfers_page = TransfersPage(driver)  # Пытаемся выполнить перевод с нулевой суммой
        transfers_page.wait_until_loaded()

        transfers_page.create_internal_transfer(
            str(source_account["id"]),
            str(target_account["id"]),
            amount
        )

        transfers_page.assert_error_message()  # Проверяем отображение ошибки

        accounts_response = api_client.get_accounts()  # Получаем обновленные счета через API

        assert accounts_response.success, f"Failed to get updated accounts: "f"{accounts_response.message}"

        accounts = accounts_response.data["accounts"]

        updated_source = next(acc for acc in accounts if acc["id"] == source_account["id"])

        updated_target = next(acc for acc in accounts if acc["id"] == target_account["id"])

        assert Decimal(str(updated_source["balance"])) == source_balance  # Проверяем, что баланс исходного счета не изменился

        assert Decimal(str(updated_target["balance"])) == target_balance # Проверяем, что баланс целевого счета не изменился
