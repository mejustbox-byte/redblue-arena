# Architecture

## Версия 0.2.0

Локальная лаборатория объединяет синтетический Red Team, нормализацию telemetry, Blue Team detection и контроль выполнения. Реальные exploit payloads, external targets и произвольные shell-команды отсутствуют.

## Офлайн поток

JSON config → validate authorization/allowlist → фиксированный Scenario → normalize Event v2 → RepeatedFailures Rule v2 → JSON report schema v2. События и отчёт создаются в памяти; CLI не хранит identity или постоянный audit.

## Control plane поток

Loopback dashboard/API → authenticate hashed bearer token → tenant Principal → RBAC/scope/quota → SQLite queued job + audit → thread pool → повторная validate → fixed worker → completed/failed/cancelled → SQLite report + audit. Tenant привязан к токену; URL/body не выбирают tenant.

| Компонент | Файл/пакет | Граница |
| --- | --- | --- |
| Контракты | modules/contracts.py | Event v2, Scenario/Detector Protocol |
| Red fixtures | modules/scenarios.py | 4 встроенных генератора, без сети |
| Blue detection | modules/detections.py | Rule v2, inclusive sliding window |
| Policy/telemetry/orchestration | core.py | Fail-closed config, bounded telemetry, report |
| Evaluation | evaluation.py | Labelled synthetic controls, confusion matrix |
| Worker protocol | worker.py | Один bounded stdin JSON → report stdout |
| Runtime | runner.py | Docker isolation или explicit trusted-local |
| Control plane/storage | control.py | SQLite transactions, tenant scopes, quotas, job lifecycle, hash-chain |
| API | web.py | Loopback, Host/Origin, bearer roles, payload/rate limits |
| UI | dashboard.py | Same-origin static HTML/JS, in-memory token, textContent |

## Схемы и совместимость

Report schema_version=2: mode=synthetic-offline, scenario, target, rule, events, findings, audit. Схема event/window и migration описаны в MODULE-API.md. Evaluation имеет самостоятельную schema_version=1; это не старый report v1.

CLI audit содержит три записи об одном запуске. Persistent audit control plane добавляет identity, lifecycle и отказы с tenant-scoped sequence/previous/digest. SQLite хранит только token hashes. На отчёты действует retention; metadata сохраняются для квот и forensic history.

## Изоляция

Docker runner не монтирует host/daemon socket, не публикует порты, отключает network, удаляет capabilities и использует read-only filesystem, non-root и resource limits. Docker host доверенный. Python Protocol не является sandbox. Trusted-local subprocess предназначен только для встроенного доверенного кода. ControlPlane Python API доверенный: сервер создаёт Principal через authenticate.

Один процесс владеет SQLite через POSIX flock; после рестарта queued/running не повторяются, а становятся failed. Лимиты, cancellation и retention описаны в OPERATIONS.md. SQLite chain не является внешним неизменяемым audit sink.

## Настройка и проверка разработки

scripts/dev.py создаёт локальный venv и вызывает те же проверки, что CI. Он не запускает постоянный server/provision и не содержит credentials. Docker gate включается явно через --docker; отсутствие Docker не заменяется доверенным runner. INSTALL.md описывает ручной запуск локальной платформы.

## Внешнее облако

Требует отдельного control-plane server с TLS/identity provider, защищённого хранилища и worker runtime/VM boundaries, централизованного аудита и эксплуатационной проверки. Текущая реализация проверяет локальные application boundaries и container worker policy; она не гарантирует изоляцию от привилегированного владельца общего Docker host.
