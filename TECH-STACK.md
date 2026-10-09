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

