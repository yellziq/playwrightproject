import logging

import allure
import pytest
from playwright.sync_api import Error, expect, sync_playwright

from core.config import Settings
from core.logging_mask import mask_credentials


@pytest.fixture(scope="session")
def settings():
    config = Settings.from_env()
    expect.set_options(timeout=config.timeout_ms)
    return config


@pytest.fixture(scope="session", autouse=True)
def mask_test_logs(request):
    original_factory = logging.getLogRecordFactory()

    def masked_record(*args, **kwargs):
        record = original_factory(*args, **kwargs)
        message = record.getMessage()
        masked = mask_credentials(message)
        if masked != message:
            record.msg = masked
            record.args = ()
        return record

    logging.setLogRecordFactory(masked_record)
    try:
        if request.config.getoption("--demo-artifacts"):
            logging.getLogger(__name__).info(
                "Демо маскирования (вымышленные данные): phone=%s email=%s otp=%s password=%s",
                "+70000000000", "demo@example.invalid", "123456", "demo-password",
            )
        yield
    finally:
        logging.setLogRecordFactory(original_factory)


@pytest.fixture(scope="session")
def browser(settings, request):
    with sync_playwright() as playwright:
        engine = getattr(playwright, settings.browser)
        with engine.launch(
            headless=not request.config.getoption("--headed"),
            slow_mo=request.config.getoption("--slow-mo"),
        ) as browser:
            yield browser


@pytest.fixture
def public_page(browser, settings):
    with browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=settings.browser != "firefox") as context:
        context.set_default_timeout(settings.timeout_ms)
        yield context.new_page()


@pytest.fixture
def desktop_page(browser, settings):
    with browser.new_context(viewport={"width": 1280, "height": 900}) as context:
        context.set_default_timeout(settings.timeout_ms)
        yield context.new_page()


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    report = yield
    if report.when == "call" and report.failed and "otp_page" in item.funcargs:
        allure.attach(
            "Страница входа и профиль могут содержать телефон, код или данные аккаунта",
            "Причина отсутствия снимка",
        )
    page = item.funcargs.get("public_page") or item.funcargs.get("desktop_page")
    demo = item.config.getoption("--demo-artifacts")
    if report.when == "call" and (report.failed or demo) and page is not None:
        try:
            # Public checks use anonymous contexts. Mask form fields even there.
            screenshot = page.screenshot(
                mask=[page.locator("input, textarea, [contenteditable='true']")],
                timeout=7000,
            )
            title = "Страница при сбое" if report.failed else "Скриншот для демонстрации"
            allure.attach(screenshot, title, allure.attachment_type.PNG)
        except Error:
            logging.getLogger(__name__).warning("Снимок страницы недоступен")
            allure.attach("Playwright не смог сделать снимок страницы", "Диагностика")
    return report


def pytest_addoption(parser):
    parser.addoption("--headed", action="store_true", help="Показать окно браузера")
    parser.addoption("--slow-mo", type=int, default=0, help="Интервал показа действий, мс")
    parser.addoption(
        "--demo-artifacts", action="store_true",
        help="Показать маскирование и приложить снимки публичных тестов",
    )
    parser.addoption(
        "--manual-otp", action="store_true", help="Открыть браузер для ручного входа по коду"
    )
    parser.addoption(
        "--manual-order-confirm", action="store_true",
        help="Дождаться ручного подтверждения заказа в браузере",
    )


@pytest.fixture
def otp_page(request, settings):
    if not request.config.getoption("--manual-otp"):
        pytest.skip("Для входа с ручным вводом кода нужен флаг --manual-otp")

    with sync_playwright() as playwright:
        engine = getattr(playwright, settings.browser)
        with engine.launch(
            headless=False, slow_mo=request.config.getoption("--slow-mo")
        ) as browser:
            with browser.new_context(viewport={"width": 1280, "height": 900}) as context:
                context.set_default_timeout(settings.timeout_ms)
                yield context.new_page()
