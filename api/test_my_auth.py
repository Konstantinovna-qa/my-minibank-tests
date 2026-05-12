from typing import Any

import pytest
from config.settings import settings, UserRole


@pytest.mark.api
@pytest.mark.auth
class TestMyAuthAPI:
    def test_my_first_api_login(self, api_client):
        """Мой первый API тест логина"""

        test_user = settings.get_user(UserRole.USER)  # Получаем тестового пользователя с ролью USER из настроек
        response = api_client.login(test_user.email, test_user.password)  # Выполняем запрос логина с email и паролем тестового пользователя

        assert response.success, f"Login failed: {response.message}"  # Проверяем, что запрос выполнен успешно
        assert response.status_code == 200  # Проверяем, что HTTP статус код равен 200

        assert 'token' in response.data, "Token field is missing in response"
        token = response.data['token']
        assert isinstance(token, str), "Token should be string"
        assert len(token) > 0, "Token should not be empty"

        assert 'user' in response.data, "User field is missing in response"  # Проверка наличия пользователя
        user_info = response.data['user']

        assert 'email' in user_info, "Email field is missing in user data"  # Проверка email
        assert user_info['email'] == test_user.email, f"Expected email {test_user.email}, got {user_info['email']}"

        assert 'role' in user_info, "Role field is missing in user data"   # Проверяем роль
        expected_role = test_user.role.value
        assert user_info['role'] == expected_role, f"Expected role {expected_role}, got {user_info['role']}"


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
