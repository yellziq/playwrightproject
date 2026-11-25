import logging
import re
from decimal import Decimal
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import expect


logger = logging.getLogger(__name__)


def ruble_amount(text):
    match = re.search(r"([0-9][0-9\s]*(?:[.,][0-9]{1,2})?)\s*₽", text)
    assert match is not None, "На странице отсутствует сумма в рублях"
    return Decimal("".join(match[1].split()).replace(",", "."))


def ruble_pattern(amount):
    integer, _, fraction = format(amount, ".2f").partition(".")
    digits = r"\s*".join(integer)
    cents = r"(?:[.,]00)?" if fraction == "00" else f"[.,]{fraction}"
    return re.compile(rf"(?<![\d.,]){digits}{cents}\s*₽")


class ShopPages:
    product_path = "/catalog/pravila/3571/"
    product_query = "Правило 1000 мм"

    def __init__(self, page, base_url):
        self.page = page
        self.base_url = base_url
        self.add_button = page.locator(".detail-buy-button:visible")
        self.cart_row = page.locator(".basket-items-list-item-container")

    def search_for_product(self):
        logger.info("Открытие главной и поиск товара")
        self.page.goto(f"{self.base_url}/", wait_until="commit")
        search = self.page.locator('input[name="q"][placeholder="Поиск товара"]:visible')
        search.fill(self.product_query)
        search.press("Enter", no_wait_after=True)
        self.page.wait_for_url("**/catalog/?q=*", wait_until="commit")
        link = self.page.locator(f'a[href="{self.product_path}"]:visible').filter(
            has_text=self.product_query
        )
        logger.info("Переход из результатов поиска в карточку")
        link.click(no_wait_after=True)
        self.page.wait_for_url(f"**{self.product_path}", wait_until="commit")

    def read_product(self):
        name = self.page.locator("h1")
        expect(name).to_contain_text(self.product_query)
        price = self.page.locator(".price-container .price:visible").first
        expect(price).to_contain_text("₽")
        return name.inner_text().strip(), ruble_amount(price.inner_text())

    def add_to_cart(self):
        logger.info("Нажатие «В корзину» в карточке товара")
        self.add_button.click()
        expect(self.page.locator(".detail-buy-button")).to_have_class(re.compile(r"\bin-basket\b"))
        logger.info("Сайт подтвердил добавление товара")

    def open_cart(self):
        logger.info("Открытие корзины")
        self.page.goto(f"{self.base_url}/personal/cart/", wait_until="commit")
        expect(self.page.locator("h1")).to_have_text("Моя корзина")

    def verify_cart(self, name, unit_price, quantity=1):
        expect(self.cart_row).to_have_count(1)
        expect(self.cart_row.locator(".basket-item-info-name-link")).to_have_text(name)
        expect(self.cart_row.locator("input.basket-item-amount-filed")).to_have_value(str(quantity))
        expect(self.cart_row.locator('[id^="basket-item-price-"]')).to_have_text(
            ruble_pattern(unit_price)
        )
        expected_total = ruble_pattern(unit_price * quantity)
        expect(self.cart_row.locator('[id^="basket-item-sum-price-"]')).to_have_text(expected_total)
        expect(self.page.locator('[data-entity="basket-total-price"]')).to_have_text(expected_total)

    def increase_cart_quantity(self):
        self.cart_row.locator('[data-entity="basket-item-quantity-plus"]').click()

    def open_checkout(self):
        self.page.locator('[data-entity="basket-checkout-button"]').click()
        expect(self.page.locator("h1")).to_have_text("Оформление заказа")


class CheckoutPage:
    order_confirmation_url = re.compile(r"[?&]ORDER_ID=[^&#]+", re.IGNORECASE)

    def __init__(self, page):
        self.page = page
        self.form = page.locator("#bx-soa-order-form")

    def choose_pickup_and_payment(self):
        pickup = self.form.locator("#ID_DELIVERY_ID_2")
        payment = self.form.locator("#ID_PAY_SYSTEM_ID_1")
        self.form.locator('#bx-soa-delivery .bx-soa-pp-company-smalltitle:text-is("Самовывоз")').click()
        expect(pickup).to_be_checked()
        if not payment.is_checked():
            self.form.locator(
                '#bx-soa-paysystem .bx-soa-pp-company-smalltitle:text-is("Оплата при получении")'
            ).click()
        expect(payment).to_be_checked()
        expect(
            self.form.locator("#bx-soa-delivery")
        ).to_contain_text("Вы можете самостоятельно забрать заказ")

    def fill_buyer(self, name, email, phone):
        self.form.locator("#soa-property-1").fill(name)
        self.form.locator("#soa-property-2").fill(email)
        self.form.locator("#soa-property-3").fill(phone)

    def verify_summary(self, name, quantity, total):
        items = self.form.locator("#bx-soa-basket")
        expect(items).to_contain_text(name)
        expect(items).to_contain_text(re.compile(rf"(?<!\d){quantity}\s*шт"))
        expect(items).to_contain_text(ruble_pattern(total))
        expect(self.page.locator("#bx-soa-total .bx-soa-cart-total-line-total")).to_contain_text(
            ruble_pattern(total)
        )

    def show_final_button(self):
        button = self.form.locator('[data-save-button="true"]')
        button.scroll_into_view_if_needed()
        expect(button).to_be_visible()

    def wait_for_order_confirmation(self, timeout_ms):
        self.page.wait_for_url(self.order_confirmation_url, timeout=timeout_ms)
        query = parse_qs(urlsplit(self.page.url).query)
        order_number = next(values[0] for key, values in query.items() if key.upper() == "ORDER_ID")
        confirmation = self.page.get_by_text(
            re.compile(rf"(?:заказ|№)[^\n]*\b{re.escape(order_number)}\b", re.IGNORECASE)
        ).filter(visible=True)
        expect(confirmation.first).to_be_visible()
