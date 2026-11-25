import allure
import pytest

from ui.pages import AuthorizationPage, CatalogPage


@allure.feature("Каталог")
@allure.title("CAT-01 · Каталог открывается")
def test_catalog_opens(public_page, settings):
    allure.dynamic.label("case_id", "CAT-01")
    catalog = CatalogPage(public_page, settings.base_url)
    with allure.step("Открыть каталог"):
        catalog.open()
    with allure.step("Проверить заголовок каталога"):
        catalog.heading.should_be_visible()


@pytest.mark.parametrize(
    "case_id, expected",
    [
        pytest.param("AUTH-01", "page", id="AUTH-01-anonymous-entry"),
        pytest.param("AUTH-02", "phone", id="AUTH-02-phone-form"),
    ],
)
@allure.feature("Авторизация")
def test_anonymous_authorization(public_page, settings, case_id, expected):
    allure.dynamic.title(f"{case_id} · " + {
        "page": "Страница входа доступна анонимному пользователю",
        "phone": "Форма предлагает ввод номера телефона",
    }[expected])
    allure.dynamic.label("case_id", case_id)
    with allure.step("Открыть страницу авторизации в новой сессии"):
        CatalogPage(public_page, settings.base_url).open_authorization()
    authorization = AuthorizationPage(public_page)
    with allure.step("Проверить страницу входа"):
        if expected == "phone":
            authorization.should_show_phone_form()
        else:
            authorization.heading.should_be_visible()
