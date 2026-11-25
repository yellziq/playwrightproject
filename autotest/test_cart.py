import allure

from ui.shop import ShopPages


@allure.feature("Корзина")
@allure.title("Поиск товара и добавление в корзину")
def test_product_in_cart(desktop_page, settings):
    allure.dynamic.label("case_id", "ТК-О08")
    shop = ShopPages(desktop_page, settings.base_url)
    with allure.step("Найти товар на главной и открыть карточку"):
        shop.search_for_product()
        name, price = shop.read_product()
    with allure.step("Добавить одну единицу в корзину"):
        shop.add_to_cart()
    with allure.step("Проверить товар, количество и сумму позиции"):
        shop.open_cart()
        shop.verify_cart(name, price)
