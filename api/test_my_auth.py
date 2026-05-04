from typing import Any

import pytest
from config.settings import settings, UserRole



@pytest.mark.api
@pytest.mark.auth
def test_my_first_api_login(api_client):
    """Мой первый API тест логина"""
    test_user = settings.get_user(UserRole.USER)
    response = api_client.login(test_user.email, test_user.password)

    assert response.success, f"Login failed: {response.message}"
    assert response.status_code == 200





@pytest.mark.api
@pytest.mark.auth
class TestMyAuthAPI:
    def test_login_wrong_password(self, api_client):
        """Тест с неправильным паролем"""

        test_user = settings.get_user(UserRole.USER)
        login_response = api_client.login(test_user.email,"All hismakesmeangry222")  # Выполняет вход с email и неверным паролем

        assert not login_response.success, "Login with invalid credentials should fail"  # Проверяет, что НЕ успешен
        assert login_response.status_code in [401, 403]  # Проверяет, что HTTP статус код ответа находится в списке [401, 403]
        data = login_response.data or {}
        assert 'token' not in data, "Token should not be present on failed login"


    def test_already_logged_in_user(self, logged_in_user):
        """Тест с уже залогиненным пользователем"""

        assert logged_in_user is not None  # Проверяем, что пользователь получен
        assert isinstance(logged_in_user, dict)   # Проверяем, что это словарь


    def test_token_validation(self, api_client):
        """Тест валидации токена"""

        test_user = settings.get_user(UserRole.USER)
        response = api_client.login(test_user.email, test_user.password)


        assert response.success, f"Login failed: {response.message}"  # Проверяем успешность логина
        assert response.status_code == 200


        assert response.data is not None   # Проверяем, что токен есть
        assert "token" in response.data


        validation_response = api_client.validate_token()  # Валидируем токен
        assert validation_response.success, f"Token validation failed: {validation_response.message}"  # Проверяем успешность валидации
        assert validation_response.status_code == 200
