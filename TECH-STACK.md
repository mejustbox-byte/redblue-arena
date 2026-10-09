# Tech stack — решение 2026-10-09

## Зафиксированный выбор

| Слой | Выбор | Обоснование и статус |
| --- | --- | --- |
| Runtime | CPython 3.12.x | Проверенный локально 3.12.14; зрелая стандартная библиотека, простой CLI |
| Пакеты | pip + venv | Стандартный инструмент, отдельное окружение; runtime-зависимостей нет |
| Тесты | unittest + subprocess smoke test | Без внешних зависимостей; проверка pipeline, отказов и CLI |
| Линтер/форматтер | Ruff 0.15.0 | Один инструмент для lint и format; точная версия dev-зависимости |
| Контейнеры | Docker / OCI, Python 3.12 slim | Непривилегированный пользователь; запуск без сети, read-only и с лимитами |
| CI | GitHub Actions, Ubuntu 24.04, Python 3.12 | Минимальные permissions, lint, format, tests и smoke; не требует секретов |
| MVP UI/storage | CLI и JSON; в памяти | Минимальная поверхность атаки, детерминированные учебные данные |
| Облачный API/БД/UI | Отложено | FastAPI, PostgreSQL и frontend рассматриваются только при появлении требований |

Python выбран для схем, синтетических сценариев и детекторов благодаря простоте проверки и поддержки. Go/Rust для этого ограниченного MVP увеличивают стоимость реализации без необходимого выигрыша. Универсальная плагинная загрузка, очереди, Kubernetes и полноценный web frontend пока не нужны.

Поддерживаемый и проверяемый runtime проекта теперь 3.12; более раннее описание 3.10+ заменено. Используйте актуальные security patch-релизы ветки 3.12 после тестирования. Для воспроизводимого production-контейнера потребуется закрепить digest проверенного образа; текущий Dockerfile — лабораторная заготовка с изменяемым тегом.

## Команды проверки

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m ruff check redblue_arena tests
python -m ruff format --check redblue_arena tests
python -m unittest discover -s tests -v
python tests/smoke.py
```

Ruff конфигурируется в `pyproject.toml`; версия закреплена в `requirements-dev.txt`. pip использует версию из выбранного venv, отдельный pin pip не нужен для MVP без runtime-зависимостей. Lock-файл runtime пока не нужен; при появлении зависимостей потребуется полный lock с hashes.

## Codex Cloud — отдельная среда

После фиксации стека создайте среду только для `mejustbox-byte/redblue-arena`. Имя: `redblue-arena-lab`; рабочая ветка — ветка проверяемого PR. Не добавляйте токены, SSH-ключи, облачные credentials или production-переменные. Agent network access должен быть отключён; загрузка dev-зависимостей допускается только на этапе setup из доверенного registry.

Setup command:

```bash
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python tests/smoke.py
```

После создания проверьте принадлежность единственному репозиторию, Python 3.12, отсутствие настроенных secrets, exit code 0 smoke test и негативные policy-тесты. Не выводите значения переменных окружения или credentials в лог.

## Статус верификации

Документация и локальный MVP проверены. Codex Cloud `redblue-arena` опубликована 2026-10-09: единственный репозиторий, доступ «Только я», без secrets/переменных, сеть ограничена preset менеджеров пакетов без дополнительных доменов. В новой задаче восстановлен commit 3658104, Python 3.12.14; lint, format, 4 unittest и smoke прошли. Это подтверждение базового commit, а не будущих изменений. Рекомендация полного отключения agent network остаётся целевым ограничением; текущий preset допускает обращения к registry. GitHub Actions CI успешно завершился для commit c082cb6 (run 37881543855). Контейнерная сборка ещё требует успешного запуска; наличие файлов конфигурации не является подтверждением их работы.

Источники: [Python venv](https://docs.python.org/3.12/tutorial/venv.html), [Ruff configuration](https://docs.astral.sh/ruff/configuration/), [Codex Cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environment).

## Расширение 0.2.0

Runtime остаётся CPython 3.12.x без сторонних пакетов. Control plane использует sqlite3, http.server, concurrent.futures и POSIX fcntl; поддерживается Linux/macOS. SQLite transactions и flock обеспечивают single-host consistency. http.server используется только на loopback; внешний production server не выбран и не развёрнут.

UI: статические HTML/JavaScript same-origin без bundler и сторонних зависимостей. Docker integration job выполняет сборку и проверку worker boundaries отдельно от unit/HTTP tests. Публичный hosting/IdP/БД за пределами одного host потребуют отдельного решения; это не скрытое изменение ранее выбранного стека.

Codex Cloud пока закреплена на проверенном базовом commit 3658104 и схеме v1. Новая версия использует schema v2 и расширенный test suite; её проверка в CI не означает автоматического обновления snapshot опубликованной среды.
