# Tech stack — версия 0.2.1

| Слой | Выбор | Статус |
| --- | --- | --- |
| Runtime | CPython 3.12.x, стандартная библиотека | Проверен Python 3.12.14, runtime dependencies отсутствуют |
| Dev environment | pip/venv, scripts/dev.py | setup/check/doctor; Ruff 0.15.0 закреплён |
| Тесты | unittest, subprocess CLI smoke | 27 default checks + 2 opt-in Docker checks, 4 CLI fixtures |
| Control plane | sqlite3, concurrent.futures, POSIX fcntl | Single-host transactions/lock, Linux/macOS |
| HTTP/UI | http.server, статические HTML/JavaScript | Только loopback, same-origin, без bundler |
| Workers | Docker/OCI, Python 3.12 slim | Non-root, read-only, network none, resource limits |
| CI | GitHub Actions, Ubuntu 24.04, Python 3.12 | Dev gate и отдельная реальная Docker integration |
| Public hosting/identity | Не выбран и не развёрнут | Требует TLS, внешний IdP и инфраструктуру из ROADMAP |

Python выбран для детерминированных fixtures и правил. Проект не загружает произвольные плагины и не требует FastAPI, PostgreSQL или Kubernetes для локальной лаборатории. Docker base tag изменяемый: source tag не закрепляет digest образа. Actions также используют major-version tags. Для production release потребуется пересмотр supply chain.

## Воспроизводимая настройка

```bash
python3.12 scripts/dev.py setup
python3.12 scripts/dev.py doctor
python3.12 scripts/dev.py check --docker
```

Setup устанавливает только dev dependency из requirements-dev.txt. Check не устанавливает пакеты и не создаёт токены или постоянные данные; тесты используют временные ресурсы с cleanup. Для Docker нужны установленный daemon и доступ к registry при build. Полный control-plane gate требует POSIX. Windows поддерживается только офлайн CLI, см. INSTALL.md.

## Codex Cloud

Среда `redblue-arena` относится только к mejustbox-byte/redblue-arena, доступ «Только я», без настроенных secrets/переменных/дополнительных доменов. Опубликованный snapshot закреплён на code commit 2f9b65104ca68d1c9595489a8d1e5798dd77d376; он предшествует финальному dev tooling и документации. В новой задаче подтвердились Python 3.12.14, lint/format, 27 passed/2 Docker skipped, 4 CLI fixtures и evaluation. Для разработки release checkout следует обновить отдельно, сохраняя чужие изменения.

Сеть ограничена preset менеджеров пакетов. Это не полное OS deny-egress среды разработки; network=none реализован отдельно для Docker worker. HTTP tests требуют loopback sockets. Docker integration проверена в CI, а не в restored Cloud. Codex Cloud не является hosting приложения.

Repository-owned setup command для нового checkout: `python3.12 scripts/dev.py setup`. Результаты и границы проверок — [VERIFICATION.md](VERIFICATION.md). Историческая baseline snapshot 3658104 проверялась отдельно до реализации платформы.

Dev/CI gate 0.2.1 дополнительно требует Node.js для --check статического dashboard JS; npm dependencies отсутствуют. Проверяются локальные Markdown-ссылки. [LOCAL-INFRA-CHECKS.md](LOCAL-INFRA-CHECKS.md) отделяет CI от приёмки конкретного host.
