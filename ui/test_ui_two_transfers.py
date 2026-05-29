
import pytest
import structlog
from decimal import Decimal
from config.settings import UserRole
from ui.pages.login_page import LoginPage
from ui.pages.dashboard_page import DashboardPage
from ui.pages.transfers_page import TransfersPage

logger = structlog.get_logger(__name__)


@pytest.mark.ui
@pytest.mark.transfers

class TestUITransfers:

    def test_basic_external_transfer_exploration(self, driver, api_client, make_user_with_account):
        """Проверка внешнего перевода между пользователями с учетом фиксированной комиссии"""

        test_data_1 = make_user_with_account(UserRole.USER, 1000, "CHECKING")  # Создаем пользователя-отправителя со счетом CHECKING и балансом 1000$
        test_data_2 = make_user_with_account(UserRole.USER, 100, "CHECKING")  # Создаем пользователя-получателя со счетом CHECKING и балансом 100$

        credentials_1 = test_data_1["credentials"]  # Получаем логин и пароль отправителя
        source_account = test_data_1["account"]  # Получаем информацию о счете отправителя
        target_account = test_data_2["account"]  # Получаем информацию о счете получателя

        source_balance_before = Decimal(str(source_account["balance"]))  # Сохраняем баланс отправителя до перевода
        target_balance_before = Decimal(str(target_account["balance"]))  # Сохраняем баланс получателя до перевода

        amount = Decimal("100")
        commission = Decimal("5")

        login_page = LoginPage(driver)  # Создаем объект страницы логина
        login_page.navigate_to()  # Открываем страницу логина
        login_page.assert_page_loaded()  # Проверяем что страница логина загрузилась

        login_page.login(  # Выполняем вход под пользователем-отправителем
            credentials_1["email"],
            credentials_1["password"]
        )

        dashboard_page = DashboardPage(driver)  # Создаем объект страницы дашборда
        dashboard_page.assert_page_loaded()  # Проверяем что дашборд загрузился
        dashboard_page.open_transfers()  # Переходим на страницу переводов
        transfers_page = TransfersPage(driver)  # Создаем объект страницы переводов
        transfers_page.assert_page_loaded()  # Проверяем что страница переводов загрузилась
        transfers_page.wait_until_loaded()  # Дополнительно ожидаем полной загрузки страницы

        transfers_page.create_external_transfer(  # Создаем внешний перевод
            str(source_account["id"]),  #
            str(target_account["account_number"]),
            amount
        )

        transfers_page.assert_success_message()  # Проверяем сообщение об успешном переводе

        accounts_response = api_client.get_accounts()  # Получаем актуальные данные по счетам через API

        assert accounts_response.success, f"Failed to get updated accounts: {accounts_response.message}"  # Проверяем что API запрос выполнился успешно

        accounts = accounts_response.data["accounts"]  # Извлекаем список счетов из ответа API

        assert any(acc["id"] == source_account["id"] for acc in accounts), f"Source account {source_account['id']} not found in API response"  # Проверяем что счет отправителя присутствует в ответе API

        assert any(acc["id"] == target_account["id"] for acc in accounts), f"Target account {target_account['id']} not found in API response"  # Проверяем что счет получателя присутствует в ответе API

        updated_source = next(acc for acc in accounts if acc["id"] == source_account["id"])  # Находим обновленный счет отправителя по ID

        updated_target = next(acc for acc in accounts if acc["id"] == target_account["id"])  # Находим обновленный счет получателя по ID

        source_balance_after = Decimal(str(updated_source["balance"]))  # Получаем баланс отправителя после перевода

        target_balance_after = Decimal(str(updated_target["balance"]))  # Получаем баланс получателя после перевода

        logger.info("External transfer completed", transfer_amount=str(amount), commission=str(commission), source_balance_before=str(source_balance_before), source_balance_after=str(source_balance_after), target_balance_before=str(target_balance_before), target_balance_after=str(target_balance_after),)  # Записываем информацию о выполненном переводе в лог

        assert source_balance_after == (source_balance_before - amount - commission)  # Проверяем что у отправителя списалась сумма перевода и комиссия

        assert target_balance_after == (target_balance_before + amount)  # Проверяем что получателю зачислилась сумма перевода
