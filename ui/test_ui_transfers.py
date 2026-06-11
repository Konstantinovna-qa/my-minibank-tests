"""
UI тесты переводов MiniBank
Переводы между счетами через пользовательский интерфейс
"""

import pytest
import structlog
from decimal import Decimal
from config.settings import settings, UserRole
from ui.pages.login_page import LoginPage
from ui.pages.dashboard_page import DashboardPage
from ui.pages.transfers_page import TransfersPage

logger = structlog.get_logger(__name__)


@pytest.mark.ui
@pytest.mark.transfers
def test_access_transfers_page(driver):
    """Тест доступа к странице переводов"""
    login_page = LoginPage(driver)
    login_page.navigate_to()
    login_page.assert_page_loaded()
    
    vip_user = settings.get_user(UserRole.VIP_USER)
    login_page.login(vip_user.email, vip_user.password)
    
    dashboard_page = DashboardPage(driver)
    dashboard_page.assert_page_loaded()
    dashboard_page.open_transfers()
    
    transfers_page = TransfersPage(driver)
    transfers_page.assert_page_loaded()
    
    assert transfers_page.is_element_visible("transfer_form"), "Transfers page not loaded properly"


@pytest.mark.ui  
@pytest.mark.transfers
def test_transfer_form_elements(driver):
    """Тест наличия элементов формы перевода"""
    login_page = LoginPage(driver)
    login_page.navigate_to()
    
    vip_user = settings.get_user(UserRole.VIP_USER)
    login_page.login(vip_user.email, vip_user.password)
    
    dashboard_page = DashboardPage(driver)
    dashboard_page.assert_page_loaded()
    dashboard_page.open_transfers()
    
    transfers_page = TransfersPage(driver)
    transfers_page.assert_page_loaded()
    
    assert transfers_page.is_element_visible("transfer_form"), "Transfer form not visible"
    
    try:
        transfers_page.enter_description("Test transfer description")
    except Exception as e:
        import structlog
        structlog.get_logger(__name__).info(f"Description field not present or not interactable: {e}")


@pytest.mark.ui
@pytest.mark.transfers
class TestUITransfers:
    def test_internal_transfer_between_own_accounts(self, driver, user_with_two_accounts):
        """Тест внутреннего перевода между собственными счетами пользователя"""
        test_data = user_with_two_accounts
        credentials = test_data["credentials"]
        source_account = test_data["source_account"]
        target_account = test_data["target_account"]

        # Вход через UI
        login_page = LoginPage(driver)
        login_page.navigate_to()
        login_page.assert_page_loaded()
        login_page.login(credentials["email"], credentials["password"])
    
        # Переходим к переводам
        dashboard_page = DashboardPage(driver)
        dashboard_page.assert_page_loaded()
        dashboard_page.open_transfers()
    
        transfers_page = TransfersPage(driver)
        transfers_page.assert_page_loaded()
    
        # Выполняем перевод
        transfer_amount = 50.0
        description = "UI Test: Transfer between own accounts"
    
        transfers_page.create_internal_transfer(
            from_account=source_account["id"],
            to_account=target_account["id"],
            amount=transfer_amount,
            description=description
        )
    
        # Проверяем успешность перевода через PageObject (стабильные селекторы)
        transfers_page.assert_success_message()

        # Проверяем, что форма остается функциональной
        assert transfers_page.is_element_immediately_visible("transfer_form"), "Форма перевода должна оставаться видимой после перевода"



    def test_basic_external_transfer_exploration(self, driver, api_client, make_user_with_account):
        """Проверка внешнего перевода между пользователями с учетом фиксированной комиссии"""

        test_data_1 = make_user_with_account(UserRole.USER, 1000, "CHECKING")  # Создаем пользователя-отправителя со счетом CHECKING и балансом 1000$
        test_data_2 = make_user_with_account(UserRole.USER, 100, "CHECKING")  # Создаем пользователя-получателя со счетом CHECKING и балансом 100$

        credentials_1 = test_data_1["credentials"]  # Получаем логин и пароль отправителя

        source_account = test_data_1["account"]  # Получаем информацию о счете отправителя
        target_account = test_data_2["account"]  # Получаем информацию о счете получателя

        source_balance_response = api_client.get_account_balance(source_account["id"])  # Запрашиваем актуальный баланс отправителя через API
        assert source_balance_response.success, f"Failed to get source balance: {source_balance_response.message}"

        target_balance_response = api_client.get_account_balance(target_account["id"])  # Запрашиваем актуальный баланс получателя через API
        assert target_balance_response.success, f"Failed to get target balance: {target_balance_response.message}"

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
            str(source_account["id"]),
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
