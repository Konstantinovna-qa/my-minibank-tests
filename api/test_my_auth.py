from typing import Any

import pytest
from config.settings import settings, UserRole
from api.test_auth import TestAuthenticationAPI
from conftest import MiniBankAPIClient


@pytest.mark.api
@pytest.mark.auth
def test_my_first_api_login(self, api_client):
    """Мой первый API тест логина"""
    test_user = settings.get_user(UserRole.USER)
    response = api_client.login(test_user.email, test_user.password)

    test_auth = TestAuthenticationAPI()

    test_auth.test_valid_login(api_client)
    test_auth.test_role_based_login(api_client)

    print(response.data)


@pytest.mark.api
@pytest.mark.auth
class TestMyAuthAPI:
    def test_login_wrong_password(self, api_client):
        """Тест с неправильным паролем"""

        response = api_client.login("user@bank.test", "All hismakesmeangry222")  # Выполняет вход с email и неверным паролем

        assert not response.success, "Login with invalid credentials should fail"  # Проверяет, что НЕ успешен
        assert response.status_code in [401, 403,]  # Проверяет, что HTTP статус код ответа находится в списке [401, 403]


        if 'token' in response.data:
            token = response.data['token']
            assert len(token) > 0, "Token should not be empty"  # Проверяет, что длина строки token больше 0 (токен не пустой)


    def test_already_logged_in_user(self, logged_in_user):
        """Тест с уже залогиненным пользователем"""

        assert logged_in_user is not None  # Проверяем, что пользователь получен
        assert isinstance(logged_in_user, dict)   # Проверяем, что это словарь

        print(logged_in_user)

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