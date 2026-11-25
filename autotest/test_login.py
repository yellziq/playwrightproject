import os

import allure

from autotest.login_flow import sign_in


@allure.feature("Авторизация")
@allure.title("ТК-А01 · Вход по существующему номеру")
@allure.label("case_id", "ТК-А01")
def test_login_with_manual_otp(otp_page, settings):
    sign_in(otp_page, settings, phone=os.getenv("SB_TEST_PHONE", ""))
