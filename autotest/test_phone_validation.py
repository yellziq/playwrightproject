import allure
import pytest

from ui.pages import AuthorizationPage, CatalogPage


@allure.feature("Авторизация")
@pytest.mark.parametrize(
    "case_id, title, digits, expected_error",
    [
        pytest.param(
            "ТК-А02", "Пустой телефон", "",
            "Логин должен быть не менее 3 символов.", id="A02-empty",
        ),
        pytest.param(
            "ТК-А03", "Слишком короткий номер", "900000000",
            "Указан некорректный номер телефона.", id="A03-short",
        ),
    ],
)
def test_invalid_phone(public_page, settings, case_id, title, digits, expected_error):
    allure.dynamic.title(f"{case_id} · {title}")
    allure.dynamic.label("case_id", case_id)
    authorization = AuthorizationPage(public_page)
    with allure.step("Открыть форму входа в новой сессии"):
        CatalogPage(public_page, settings.base_url).open_authorization()
        authorization.should_show_phone_form()
    with allure.step(f"{title}. Отметить согласие"):
        authorization.enter_phone(digits)
        authorization.accept_policy()
    with allure.step("Нажать «Продолжить» и проверить текст ошибки"):
        authorization.submit_invalid_phone(expected_error)
