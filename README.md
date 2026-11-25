# UI-автотесты «Стройбаза №1»

Проект на Python, Playwright и pytest для сайта [«Стройбаза №1»](https://s-b-1.ru/). В проекте 8 тестов: 6 выполняются автоматически, а для успешного входа и подтверждения заказа нужны действия пользователя. Результаты сохраняются в Allure.

## Подготовка


SB_TIMEOUT_MS=45000 .venv/bin/python -m pytest -vs --headed --slow-mo 250 --manual-otp --manual-order-confirm --alluredir=allure-results --clean-alluredir


Откройте терминал в корне репозитория. При первом запуске установите зависимости и Chromium:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m playwright install chromium
```

Для сборки HTML-отчёта нужны Java и Allure CLI 2.34.1. Проверьте установку командами `java -version` и `allure --version`.

## Порядок запуска

Запускайте команды по очереди из корня проекта. `--headed` открывает браузер, а `--slow-mo 250` замедляет действия Playwright, чтобы их было видно. Первая команда очищает предыдущие результаты Allure, остальные добавляют результаты к этому прогону.

### 1. Открытие страниц — 3 теста

В [autotest/test_public.py](autotest/test_public.py):

- **CAT-01** открывает каталог и проверяет заголовок «Каталог».
- **AUTH-01** открывает страницу входа и проверяет заголовок «Авторизация».
- **AUTH-02** проверяет, что на странице входа видно поле «Телефон».

```bash
SB_TIMEOUT_MS=45000 .venv/bin/python -m pytest -v autotest/test_public.py --headed --slow-mo 250 --demo-artifacts --alluredir=allure-results --clean-alluredir
```

В терминале появится строка `phone=*** email=*** otp=*** password=***`. Она показывает, как [функция маскирования](core/logging_mask.py) обрабатывает вымышленные данные перед записью в лог.

### 2. Ошибки входа — 2 теста

В [autotest/test_phone_validation.py](autotest/test_phone_validation.py):

- **ТК-А02** оставляет телефон пустым, отмечает согласие, нажимает «Продолжить» и проверяет сообщение «Логин должен быть не менее 3 символов.»
- **ТК-А03** вводит короткий номер, отмечает согласие, нажимает «Продолжить» и проверяет сообщение «Указан некорректный номер телефона.»

```bash
SB_TIMEOUT_MS=45000 .venv/bin/python -m pytest -v autotest/test_phone_validation.py --headed --slow-mo 250 --demo-artifacts --alluredir=allure-results
```

Оба сценария вводят тестовые данные автоматически. Для показа скриншота в Allure подойдёт ТК-А02.

### 3. Поиск и корзина — 1 тест

В [autotest/test_cart.py](autotest/test_cart.py) программа ищет «Правило 1000 мм» на главной, открывает карточку товара, добавляет одну штуку и сверяет название, количество и сумму позиции в корзине.

```bash
SB_TIMEOUT_MS=45000 .venv/bin/python -m pytest -v autotest/test_cart.py --headed --slow-mo 250 --demo-artifacts --alluredir=allure-results
```

### 4. Успешный вход — 1 тест

В [autotest/test_login.py](autotest/test_login.py) находится **ТК-А01**. Введите номер телефона и полученный код в браузере. Программа сама отметит согласие, нажмёт «Продолжить» на обоих шагах и проверит наличие ссылки «Выйти» в личном кабинете. Флаг `--manual-otp` уже открывает видимый браузер.

```bash
SB_TIMEOUT_MS=45000 .venv/bin/python -m pytest -v autotest/test_login.py --manual-otp --alluredir=allure-results
```

### 5. Заказ с самовывозом — 1 тест

В [autotest/test_order.py](autotest/test_order.py) находится **ТК-О22**. Перед запуском корзина аккаунта должна быть пустой.

```bash
SB_TIMEOUT_MS=45000 .venv/bin/python -m pytest -vs autotest/test_order.py --manual-otp --manual-order-confirm --alluredir=allure-results
```

1. В терминале введите телефон, имя и фамилию получателя, затем email. Символы при вводе скрыты.
2. В браузере введите полученный код. Программа сама подставит телефон, найдёт товар, добавит две штуки, выберет самовывоз и оплату при получении, заполнит форму и сверит сумму.
3. Программа остановится у кнопки «Оформить заказ». Нажимайте её только если хотите отправить реальный заказ в магазин. После вашего клика тест проверит появление номера заказа. Для показа до отправки можно завершить прогон на этом шаге, тогда номер заказа останется непроверенным.

## Отчёт Allure

После запуска соберите свежий HTML-отчёт и откройте его. Команда `open` предназначена для macOS.

```bash
allure generate --single-file --clean -o allure-report allure-results
open allure-report/index.html
```

Если на этом Mac Allure CLI доступен только из временной установки, замените `allure` на `/tmp/allure-2.34.1/bin/allure`.

В отчёте откройте **Suites → ТК-А02 · Пустой телефон → Скриншот для демонстрации**. Флаг `--demo-artifacts` добавляет скриншоты публичных тестов даже при успешном результате. При падении публичного теста снимок прикрепляется и без флага, если страницу удалось захватить. Для сценариев с личным аккаунтом вместо снимка при сбое указывается причина, поскольку страница может содержать личные данные.

## Где показать локаторы

- [ui/pages.py](ui/pages.py) — класс `AuthorizationPage`. Селектор `input[placeholder="Телефон"]` находит поле телефона, а `#bx-authorize-policy-checkbox` — галочку согласия.
- [ui/shop.py](ui/shop.py) — классы `ShopPages` и `CheckoutPage` с локаторами поиска, корзины и оформления.
