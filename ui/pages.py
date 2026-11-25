import logging
import re

from playwright.sync_api import Locator, TimeoutError, expect


logger = logging.getLogger(__name__)


class BaseElement:
    def __init__(self, locator: Locator):
        self.locator = locator

    def should_be_visible(self):
        expect(self.locator).to_be_visible()


class CatalogPage:
    def __init__(self, page, base_url):
        self.page = page
        self.base_url = base_url
        self.heading = BaseElement(page.locator("h1").filter(has_text=re.compile(r"^Каталог", re.I)))

    def open(self):
        logger.info("Открытие каталога")
        response = self.page.goto(f"{self.base_url}/catalog/", wait_until="domcontentloaded")
        assert response is not None and response.ok, "Каталог не вернул успешный HTTP-ответ"

    def open_authorization(self):
        logger.info("Открытие страницы авторизации")
        # The site exposes the link in its mobile menu. Its destination is /auth/.
        response = self.page.goto(f"{self.base_url}/auth/", wait_until="commit")
        assert response is not None and response.ok, "Страница входа не вернула успешный HTTP-ответ"


class AuthorizationPage:
    def __init__(self, page):
        self.page = page
        self.heading = BaseElement(page.locator("h1").filter(has_text=re.compile(r"^Авторизация$")))
        form = page.locator("[id^='bx-authorization-']")
        self.form = form
        self.continue_button = form.locator('button:text-is("Продолжить")')
        self.phone = BaseElement(form.locator('input[placeholder="Телефон"]'))

    def should_show_phone_form(self):
        self.heading.should_be_visible()
        self.phone.should_be_visible()

    def enter_phone(self, digits):
        self.phone.locator.click()
        self.phone.locator.press_sequentially(digits)

    def submit_invalid_phone(self, expected_error):
        self.continue_button.click()
        expect(self.form.locator(".error-text")).to_have_text(expected_error)
        self.phone.should_be_visible()

    def continue_after_phone_entry(self, timeout_ms, digits=""):
        if digits:
            national_number = re.sub(r"\D", "", digits)
            if len(national_number) == 11 and national_number.startswith(("7", "8")):
                national_number = national_number[1:]
            if not re.fullmatch(r"[0-9]{10}", national_number):
                raise ValueError("Номер для входа должен содержать 10 цифр после +7")
            self.enter_phone(national_number)
        else:
            self.phone.locator.click()
        self.page.wait_for_function(
            r"""() => {
                const phone = document.querySelector(
                    '[id^="bx-authorization-"] input[placeholder="Телефон"]'
                );
                return phone && /^\+7 \(\d{3}\) \d{3}-\d{2}-\d{2}$/.test(phone.value);
            }""",
            timeout=timeout_ms,
        )
        self.accept_policy()
        self.continue_button.click()

    def accept_policy(self):
        checkbox = self.form.locator("#bx-authorize-policy-checkbox")
        if not checkbox.is_checked():
            # The actual input is hidden. The label draws the checkbox at
            # its left edge and contains a separate link to the policy.
            label = self.form.locator('label[for="bx-authorize-policy-checkbox"]')
            label.click(position={"x": 8, "y": 8})
            expect(checkbox).to_be_checked()

    def submit_code_after_entry(self, timeout_ms):
        # The user can submit from the browser before Playwright reaches the
        # button. In that case the redirect is also a valid next state.
        state = self.page.wait_for_function(
            r"""() => {
                const form = document.querySelector('[id^="bx-authorization-"]');
                if (!form || !form.getClientRects().length) return 'left-form';
                const label = [...form.querySelectorAll('label')].find(
                    node => node.textContent.trim() === 'Введите код'
                );
                const input = label?.closest('.form-group')?.querySelector('input.form-control');
                if (!input) return false;
                const button = [...form.querySelectorAll('button')].find(
                    node => node.textContent.trim() === 'Продолжить'
                );
                if (!button || button.disabled) return false;
                if (/^[0-9]{6}$/.test(input.value)) return 'ready';
                if (input.value === '' && document.activeElement !== input) input.focus();
                return false;
            }""",
            timeout=timeout_ms,
        )
        if state.json_value() == "ready":
            try:
                self.continue_button.click(no_wait_after=True, timeout=3000)
            except TimeoutError:
                if self.form.is_visible():
                    raise

    def wait_for_login(self, timeout_ms):
        # The phone form also disappears during OTP entry. Leave the auth page
        # only after the entire authorization component is gone.
        form = self.page.locator("[id^='bx-authorization-']")
        form.wait_for(state="hidden", timeout=timeout_ms)


class ProfilePage:
    def __init__(self, page, base_url):
        self.page = page
        self.url = f"{base_url}/personal/"
        self.logout = page.locator('a[href*="logout=yes"]')

    def verify_session(self):
        response = self.page.goto(self.url, wait_until="domcontentloaded")
        assert response is not None and response.ok, "Личный кабинет недоступен"
        # Use a count so a failure never prints a logout URL with a session ID.
        assert self.logout.count() > 0, "В личном кабинете отсутствует ссылка выхода"
