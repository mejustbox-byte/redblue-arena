# RedBlue Arena 0.2.0 — локальная лабораторная платформа

Выпуск для доверенного Linux/macOS host с Python 3.12.x. Сценарии генерируют только синтетические события; реальные атаки и внешние цели не поддерживаются.

- Четыре сценария, rule v2 с configurable threshold/window и synthetic fixture evaluation.
- Module API v2; JSON report schema v2, новые timestamps и rule/window metadata. Старые четырёхполевые configs совместимы; потребителям report v1 нужна миграция из MODULE-API.md.
- SQLite control plane, hashed bearer tokens, tenant-scoped RBAC/scope, квоты, очередь, отмена, timeout и restart без replay.
- Docker workers: network none, non-root, read-only, capabilities dropped и лимиты ресурсов; отсутствие Docker приводит к отказу. trusted-local доступен явно только для доверенных встроенных модулей.
- Loopback dashboard/API, постоянный hash-chain audit и ручная очистка устаревших отчётов.
- Repository-owned setup/check/doctor; CI проверяет lint/format, 27 default tests, 4 CLI fixtures, evaluation, container build и 2 реальные Docker integration tests.

Начало работы из исходников:

```bash
python3.12 scripts/dev.py setup
python3.12 scripts/dev.py check --docker
```

Provision и запуск dashboard описаны в INSTALL.md. Setup не создаёт токены, базу или сервер. Источники релиза предоставлены стандартными архивами GitHub; готовый container image/пакет PyPI не публикуются.

Public cloud hosting не входит в выпуск. HTTP слушает только 127.0.0.1; TLS/IdP, отдельные tenant VM, внешний immutable audit, автоматический retention и независимый security/load audit остаются в ROADMAP.md. Hash-chain не защищает от владельца хоста. Docker base image использует изменяемый tag. Нулевой FP на четырёх synthetic fixtures не оценивает эффективность на реальном трафике. Codex Cloud является средой разработки, его snapshot закреплён до финальных dev tooling/doc changes.
