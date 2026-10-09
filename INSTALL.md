# Installation

## Локальная лаборатория

Требуется Python 3.12.x. Дополнительные пакеты и облачные учётные данные не нужны.

```bash
git clone https://github.com/mejustbox-byte/redblue-arena.git
cd redblue-arena
python3 -m venv .venv
source .venv/bin/activate
python3 -m unittest discover -s tests -v
python3 -m redblue_arena --config examples/lab.json > report.json
```

Windows: активируйте окружение через `.venv\Scripts\activate`.

## Конфигурация

Скопируйте `examples/lab.json`. Укажите своё явное разрешение в `authorized`, учебные идентификаторы в `allowed_targets`, выбранную `target` и сценарий `failed-logins`. Разрешены только идентификаторы `lab://` с непустым суффиксом из строчных латинских букв, цифр, дефиса и подчёркивания. Не указывайте IP, URL, пароли или реальные логи.

Успешный запуск возвращает код 0 и JSON в stdout: 6 событий, 1 finding и 3 записи аудита. Недопустимая конфигурация возвращает код 2 и JSON с причиной в stderr; сценарий не запускается. Размер конфигурации ограничен 64 KiB.

## Облако

Облачный сервис пока не готов. CLI можно выполнять в изолированной учебной VM с Python без входящих портов и без сетевого доступа. Развёртывание публичного API будет отдельным этапом после RBAC, квот и контроля egress.

## Пример настроенной лаборатории

```json
{
  "authorized": true,
  "allowed_targets": ["lab://training", "lab://demo"],
  "target": "lab://demo",
  "scenario": "failed-logins"
}
```

Все четыре поля обязательны. Дополнительные поля отклоняются. Идентификатор не длиннее 128 символов; allowlist содержит 1–100 записей. Имя сценария выбирается из фиксированного реестра. Не добавляйте сетевые разрешения для этого примера: он работает полностью офлайн.

## Проверка результата и диагностика

В `report.json` должны быть `schema_version: 1`, `mode: synthetic-offline`, шесть `events`, одна запись `findings` с `count: 6` и `threshold: 5`, три записи `audit`.

| Симптом | Что проверить |
| --- | --- |
| Python не найден | Установлен ли Python 3.12.x и доступна ли команда python3 |
| No module named redblue_arena | Запускается ли команда из корня репозитория |
| Explicit laboratory authorization is required | Явное разрешение `authorized: true` |
| Target is outside the allowlist | Точное совпадение target с записью allowlist |
| Unknown scenario | Сценарий `failed-logins` |
| Ошибка JSON или чтения | Синтаксис, права и путь конфигурации |

Отчёты и конфигурации храните в учебном окружении. Перед публикацией проверьте их содержимое. CLI не создаёт сервис и не требует открытия портов.

## Dev tools и контейнер

Установка dev-инструментов и проверки описаны в [TECH-STACK.md](TECH-STACK.md). Runtime остаётся без сторонних пакетов.

```bash
docker build -t redblue-arena:lab .
docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --pids-limit 64 --memory 128m --cpus 1 redblue-arena:lab
```

Сборка требует доступа к registry образов. Dockerfile ещё не проверен сборкой в текущей среде; доступного Docker здесь нет. Не публикуйте порты.
