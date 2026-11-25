import logging

import allure
import pytest
from playwright.sync_api import Error, TimeoutError

from ui.pages import AuthorizationPage, CatalogPage, ProfilePage


logger = logging.getLogger(__name__)


def sign_in(page, settings, phone=""):
    authorization = AuthorizationPage(page)
    with allure.step("Открыть форму входа в новой сессии"):
        CatalogPage(page, settings.base_url).open_authorization()
        authorization.should_show_phone_form()

    with allure.step("Дождаться ввода телефона, подтвердить согласие и продолжить"):
        if not phone:
            logger.info("Введите номер в открытом браузере. На ввод отведено 3 минуты.")
        try:
            authorization.continue_after_phone_entry(timeout_ms=180_000, digits=phone)
        except TimeoutError:
            pytest.fail("Не удалось продолжить после ввода телефона", pytrace=False)
        except Error:
            pytest.fail("Браузер прервал ввод телефона", pytrace=False)

    with allure.step("Дождаться ввода кода и нажать «Продолжить»"):
        logger.info("Введите полученный шестизначный код в браузере.")
        try:
            authorization.submit_code_after_entry(timeout_ms=180_000)
        except (AssertionError, Error):
            pytest.fail("Не удалось подтвердить код за отведённое время", pytrace=False)

    with allure.step("Дождаться завершения входа"):
        try:
            authorization.wait_for_login(timeout_ms=settings.timeout_ms)
        except TimeoutError:
            pytest.fail("После отправки кода форма входа осталась открыта", pytrace=False)
        except Error:
            pytest.fail("Браузер прервал ожидание входа", pytrace=False)

    with allure.step("Подтвердить активную сессию в личном кабинете"):
        try:
            ProfilePage(page, settings.base_url).verify_session()
        except Error:
            pytest.fail("Не удалось открыть личный кабинет", pytrace=False)
