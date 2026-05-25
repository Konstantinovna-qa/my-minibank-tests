import pytest

from ui.pages.login_page import LoginPage
from ui.pages.dashboard_page import DashboardPage
from ui.pages.transfers_page import TransfersPage


@pytest.mark.ui
@pytest.mark.transfers
class TestUITransfers:

    def test_simple_transfer_between_accounts(self, driver, api_client, user_with_two_accounts):
        """Проверка успешного перевода между счетами пользователя через UI"""

        source_account = user_with_two_accounts["source_account"]
        target_account = user_with_two_accounts["target_account"]
        credentials = user_with_two_accounts["credentials"]

        source_balance = source_account["balance"]
        target_balance = target_account["balance"]

        amount = 50

        login_page = LoginPage(driver)  # Логинимся
        login_page.navigate_to()
        login_page.assert_page_loaded()
        login_page.login(credentials["email"], credentials["password"])

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

        transfers_page.assert_success_message()  # Проверяем сообщение об успехе

        accounts = api_client.get_accounts().data["accounts"]  # Получаем обновленные счета через API

        updated_source = next(acc for acc in accounts if acc["id"] == source_account["id"])
        updated_target = next(acc for acc in accounts if acc["id"] == target_account["id"])

        assert float(updated_source["balance"]) == float(source_balance) - amount  # Проверяем, что баланс списался и зачислился
        assert float(updated_target["balance"]) == float(target_balance) + amount

    def test_transfer_insufficient_funds(self, driver, api_client, user_with_two_accounts):
        """Проверка ошибки перевода через UI при недостаточном балансе"""

        source_account = user_with_two_accounts["source_account"]
        target_account = user_with_two_accounts["target_account"]
        credentials = user_with_two_accounts["credentials"]

        source_balance = source_account["balance"]
        target_balance = target_account["balance"]

        amount = 100

        login_page = LoginPage(driver)  # Логинимся
        login_page.navigate_to()
        login_page.assert_page_loaded()
        login_page.login(credentials["email"], credentials["password"])

        dashboard_page = DashboardPage(driver)  # Открываем страницу переводов
        dashboard_page.assert_page_loaded()
        dashboard_page.open_transfers()

        transfers_page = TransfersPage(driver)  # Пытаемся перевести деньги со счета без денег
        transfers_page.wait_until_loaded()
        transfers_page.create_internal_transfer(
            str(target_account["id"]),
            str(source_account["id"]),
            amount
        )

        transfers_page.assert_error_message()  # Проверяем сообщение об ошибке

        accounts = api_client.get_accounts().data["accounts"]  # Получаем обновленные счета через API

        updated_source = next(acc for acc in accounts if acc["id"] == source_account["id"])
        updated_target = next(acc for acc in accounts if acc["id"] == target_account["id"])

        assert float(updated_source["balance"]) == float(source_balance)  # Проверяем, что балансы не изменились
        assert float(updated_target["balance"]) == float(target_balance)

    def test_transfer_with_zero_amount_should_fail(self, driver, api_client, user_with_two_accounts):
        """Проверка ошибки перевода при вводе нулевой суммы"""

        source_account = user_with_two_accounts["source_account"]
        target_account = user_with_two_accounts["target_account"]
        credentials = user_with_two_accounts["credentials"]

        source_balance = source_account["balance"]
        target_balance = target_account["balance"]

        amount = "0"

        login_page = LoginPage(driver)  # Логинимся
        login_page.navigate_to()
        login_page.assert_page_loaded()
        login_page.login(credentials["email"], credentials["password"])

        dashboard_page = DashboardPage(driver)  # Открываем страницу переводов
        dashboard_page.assert_page_loaded()
        dashboard_page.open_transfers()

        transfers_page = TransfersPage(driver)  # Пытаемся ввести отрицательное число
        transfers_page.wait_until_loaded()
        transfers_page.create_internal_transfer(
            str(source_account["id"]),
            str(target_account["id"]),
            amount
        )

        transfers_page.assert_error_message()  # Проверяем сообщение об ошибке

        accounts = api_client.get_accounts().data["accounts"]  # Получаем обновленные счета через API

        updated_source = next(acc for acc in accounts if acc["id"] == source_account["id"])
        updated_target = next(acc for acc in accounts if acc["id"] == target_account["id"])

        assert float(updated_source["balance"]) == float(source_balance)  # Проверяем, что балансы не изменились
        assert float(updated_target["balance"]) == float(target_balance)
