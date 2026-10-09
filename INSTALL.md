# Installation

## Runtime и проверки

CLI: CPython 3.12.x. Control plane: Linux или macOS (POSIX file locking); Windows поддерживается только для офлайн CLI. Dev-зависимость — Ruff 0.15.0.

```bash
git clone https://github.com/mejustbox-byte/redblue-arena.git
cd redblue-arena
python3.12 scripts/dev.py setup
source .venv/bin/activate
python3.12 scripts/dev.py doctor
python3.12 scripts/dev.py check
```

Для воспроизводимой версии используйте `git checkout v0.2.0` после публикации тега; разработку продолжайте в отдельной ветке от main. Setup проверяет Python до изменений, создаёт `.venv`, устанавливает Ruff и запускает lint/format, unit/HTTP, CLI smoke и evaluation. Повторный setup не удаляет окружение. `check` не устанавливает пакеты; переменная REDBLUE_DOCKER_TESTS не включает Docker незаметно. Сетевой доступ нужен для pip, а с `--docker` — для сборки базового образа. Настройка не создаёт identity, базу или постоянный сервер.

На Windows доступен только офлайн CLI: вручную создайте venv через Python 3.12, установите requirements-dev.txt и активируйте `.venv\Scripts\activate`. Полная команда setup/check и control-plane тесты требуют POSIX. Не копируйте venv между ОС или checkout: создайте его заново в новом каталоге.

## Конфигурация сценария

Четыре обязательных поля: `authorized`, `allowed_targets`, `target`, `scenario`. Дополнительно допускается `rule` с ровно четырьмя полями: rule_id, version, threshold, window_ms. Другие поля отклоняются.

- `authorized` строго true; allowlist содержит 1–100 идентификаторов `lab://` с суффиксом из строчных латинских букв, цифр, дефиса и подчёркивания, до 128 символов.
- target должен точно совпадать с allowlist. Сценарии перечислены в README.
- rule_id фиксирован: `auth.repeated_failures`; version: 2; threshold: целое 2–100; window_ms: целое 1000–3600000. Boolean не принимается как число.
- По умолчанию: threshold 5, window_ms 60000. Граница окна включена.

```bash
python -m redblue_arena --config examples/lab.json
python -m redblue_arena --config examples/spread.json
python -m redblue_arena --config examples/window.json
python -m redblue_arena --config examples/lab.json --evaluate
```

Успех: код 0, JSON stdout. Отказ: код 2, JSON stderr. Ввод ограничен 64 KiB. JSON-отчёт сценария имеет schema_version 2; evaluation имеет отдельную schema_version 1. `examples/window.json` даёт 0 findings, потому что в окне 3 секунды не помещается 5 ошибок.

## Локальный dashboard и API

Сначала подготовьте приватный каталог и создайте identity. Команда выдаёт токен один раз; редирект сохраняет его локально, а не в shell history.

```bash
umask 077
mkdir -p .lab
python -m redblue_arena.web --db .lab/arena.sqlite provision --tenant training --subject operator --role admin --target lab://training > .lab/operator.token
```

Для отдельного viewer повторите provision с `--subject observer --role viewer` и сохраните в другом `.token`. Для одного tenant список целей должен совпадать; provision не меняет существующий scope. Остановите сервер перед provision/revoke: одна база допускает один control-plane процесс.

Рекомендуемый изолированный режим:

```bash
docker build -t redblue-arena:lab .
python -m redblue_arena.web --db .lab/arena.sqlite serve --runner docker
```

Откройте `http://127.0.0.1:8765`, вставьте токен из приватного файла в поле доступа. Выберите сценарий, цель и подтвердите scope. Задания, JSON-отчёты, отмена, аудит и retention доступны в dashboard. Токен хранится только в памяти вкладки и очищается кнопкой «Выйти».

Если Docker не установлен, только для доверенных встроенных модулей:

```bash
python -m redblue_arena.web --db .lab/arena.sqlite serve --runner trusted-local
```

Этот режим не даёт ОС-изоляции и не предназначен для внешних пользователей. Сервер намеренно нельзя привязать к `0.0.0.0`. HTTP loopback не заменяет TLS; не публикуйте порт через tunnel/proxy. Удалённое облако рассматривается отдельно в OPERATIONS.

## Контейнерные проверки

```bash
docker build -t redblue-arena:lab .
REDBLUE_DOCKER_TESTS=1 python -m unittest discover -s tests -p test_runner.py -v
# Полный dev gate, включая build и Docker integration:
python3.12 scripts/dev.py check --docker
```

Интеграционные проверки запускают реальный worker и проверяют non-root, read-only filesystem и отсутствие сетевой достижимости. Без флага 2 Docker-теста явно skipped. GitHub Actions содержит отдельный Docker job.

## Диагностика

| Симптом | Проверка |
| --- | --- |
| No module named redblue_arena | Запуск из корня checkout и правильный Python |
| Role/scope отказ | Роль admin/analyst, tenant allowlist и подтверждение scope |
| Worker failed | Docker daemon доступен; образ redblue-arena:lab собран; нет автоматического pull |
| Database already in use | Остановите другой процесс, работающий с этой базой |
| 429 | До 2 активных заданий на tenant, 100 заданий за 24 часа; HTTP до 120 запросов/мин глобально |
| Audit integrity check failed | Остановите изменения и проверьте резервную копию; не сбрасывайте chain |

Данные `.lab`, `.token`, SQLite и отчёты исключены из git. Не используйте реальные credentials или production-телеметрию в тестах и примерах.
