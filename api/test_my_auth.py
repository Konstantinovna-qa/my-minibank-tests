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



@pytest.mark.api
@pytest.mark.auth
class TestMyAuthAPI:

    @pytest.mark.parametrize("role", [
        UserRole.USER,
        UserRole.VIP_USER,
        UserRole.ADMIN,
        UserRole.SUPPORT
    ], ids=["login_user", "login_vip_user", "login_admin", "login_support"])
    def test_login_different_roles(self, api_client, role):
        """Тест логина разных ролей через параметризацию"""
        user = settings.get_user(role)
        response = api_client.login(user.email, user.password)

        assert response.success  #Проверяем, что логин успешный
        assert response.data is not None, "Response data is None"  # Проверяем, что данные существуют
        assert 'user' in response.data, "Response missing 'user' field"  # Проверяем, что есть поле 'user'
        assert response.data['user']['role'] == role.value  # Сравниваем роли



    @pytest.mark.parametrize(
        "role",
        [UserRole.USER, UserRole.ADMIN],
        ids=["user", "admin"]
    )
    @pytest.mark.parametrize(
        "password_type",
        ["valid", "invalid"],
        ids=["correct_password", "wrong_password"]
    )
    def test_login(self, role, password_type, api_client):
        """Два декоратора на одном тесте"""
        user = settings.get_user(role)

        if password_type == "valid":
            password = user.password
            expected = True
        else:
            password = "wrong_password"
            expected = False

        response = api_client.login(user.email, password)

        assert response.success == expected

    @pytest.mark.parametrize(
        "email, password, expected_status",
        [
            ("invalid@email.com", "wrongpassword", 401),
            ("", "wrongpassword", 400),
            ("invalid@email.com", "", 400),
            ("", "", 400),
            ("wrong_format_email", "password123", 400),
        ],
        ids=[
            "invalid_email_and_password",
            "empty_email",
            "empty_password",
            "empty_email_and_password",
            "invalid_email_format"
        ]
    )
    def test_login_errors(self, api_client, email, password, expected_status):
        """Параметризированный тест ошибок логина"""

        response = api_client.login(email, password)

        assert not response.success, "Логин с невалидными данными должен завершиться ошибкой"

        assert response.status_code == expected_status, f"Ожидался статус {expected_status}, но получен {response.status_code}"

        assert response.data is None or response.data == {}, f"При ошибке логина данные пользователя не должны возвращаться"