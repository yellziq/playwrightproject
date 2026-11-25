import logging
import os
from getpass import getpass

import allure
import pytest
from playwright.sync_api import Error

from autotest.login_flow import sign_in
from ui.shop import CheckoutPage, ShopPages


logger = logging.getLogger(__name__)


def buyer_data(variable, prompt):
    value = os.getenv(variable, "").strip() or getpass(f"{prompt} (ввод скрыт): ").strip()
    if not value:
        pytest.fail(f"Заполните {variable}", pytrace=False)
    return value


@allure.feature("Заказ")
@allure.title("ТК-О22 · Самовывоз с ручным подтверждением")
@allure.label("case_id", "ТК-О22")
def test_pickup_order(request, otp_page, settings):
    if not request.config.getoption("--manual-order-confirm"):
        pytest.skip("Для оформления с ручным подтверждением нужен флаг --manual-order-confirm")

    phone = buyer_data("SB_TEST_PHONE", "Ваш телефон")
    name = buyer_data("SB_ORDER_NAME", "Имя и фамилия получателя")
    email = buyer_data("SB_ORDER_EMAIL", "Электронная почта получателя")

    sign_in(otp_page, settings, phone=phone)
    shop = ShopPages(otp_page, settings.base_url)
    checkout = CheckoutPage(otp_page)
    with allure.step("Проверить, что корзина аккаунта пуста"):
        shop.open_cart()
        if shop.cart_row.count():
            pytest.fail("Перед прогоном освободите корзину аккаунта вручную", pytrace=False)

    with allure.step("Найти товар на главной и открыть карточку"):
        shop.search_for_product()
        product, unit_price = shop.read_product()

    with allure.step("Добавить товар и сверить корзину для двух единиц"):
        shop.add_to_cart()
        shop.open_cart()
        shop.verify_cart(product, unit_price)
        shop.increase_cart_quantity()
        shop.verify_cart(product, unit_price, quantity=2)

    with allure.step("Оформление — самовывоз, оплата при получении и данные покупателя"):
        shop.open_checkout()
        checkout.choose_pickup_and_payment()
        try:
            checkout.fill_buyer(name, email, phone)
        except Error:
            pytest.fail("Не удалось заполнить данные покупателя", pytrace=False)
        checkout.verify_summary(product, 2, unit_price * 2)

    with allure.step("Дождаться ручного подтверждения и проверить номер заказа"):
        checkout.show_final_button()
        logger.info("Проверьте данные и сумму в браузере. Финальную кнопку «Оформить заказ» нажимаете вы.")
        try:
            checkout.wait_for_order_confirmation(timeout_ms=180_000)
        except (Error, AssertionError):
            pytest.fail("Подтверждение с номером заказа не обнаружено", pytrace=False)
