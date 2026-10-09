# Проверки локальной инфраструктуры — 0.2.1

Этот список дополняет автоматические тесты и фиксирует то, что CI не подтверждает для конкретного компьютера. Статус всех ручных проверок ниже: **не выполнено на пользовательском host**. Релиз локальной платформы не означает приёмку инфраструктуры или публичного сервиса.

## Автоматический gate

Из корня checkout на POSIX с Python 3.12.x, Node.js и работающим Docker:

```bash
python3.12 scripts/dev.py setup
python3.12 scripts/dev.py check --docker
```

Без `--docker`: 29 tests discovered, 27 выполняются, 2 явно skipped. С Docker: дополнительно выполняются 5 runner tests, из них 3 повторяют default suite, 2 проверяют реальные контейнеры. Итого 29 уникальных тестов, а не 34. Gate также проверяет pip, Ruff, четыре CLI fixtures, evaluation, локальные Markdown-ссылки и синтаксис dashboard JS. JS syntax check не является browser E2E.

Docker job в GitHub Actions подтверждает boundary tests на CI host; локальный daemon/kernel/Desktop на пользовательском host требуют отдельного запуска. Docker устанавливается оператором из официального источника; setup его не устанавливает. Node используется только для dev syntax check, runtime приложения остаётся Python stdlib.

## Приёмка конкретного host

| Проверка | Действия | Критерий и evidence |
| --- | --- | --- |
| Runtime/зависимости | `python3.12 scripts/dev.py doctor`, затем setup/check | Python 3.12, POSIX, pip/Ruff/test exit 0; сохранить версии ОС/Python/Node/Docker без env dump |
| Реальный Docker daemon | `docker version`, `python3.12 scripts/dev.py check --docker` | Build и оба Docker integration tests passed; отсутствуют skipped в отдельном runner gate |
| Loopback bind | Provision/serve по INSTALL.md; проверить слушающие сокеты через системный инструмент (`lsof -nP -iTCP:8765 -sTCP:LISTEN` на macOS или `ss -ltnp` на Linux) | Только 127.0.0.1:8765; порт не опубликован через tunnel/proxy; сохранить обезличенный результат |
| Browser E2E | Открыть 127.0.0.1:8765; admin login, scope checkbox, submit, refresh, report, audit, logout; повторить viewer | Admin видит terminal report/audit; viewer не создаёт/cancel/prune; после logout доступ очищен; screenshot без token |
| Browser storage/headers | Через DevTools проверить application storage и response headers; перезагрузить вкладку после logout | Нет token в localStorage/URL; no-store/CSP/nosniff; token нужно вводить заново; не экспортировать HAR с Authorization |
| Права на данные | Provision при umask 077; проверить права каталога .lab, DB/token и backup | Только оператор читает данные; не хранить каталог в общедоступной синхронизации и не публиковать token stdout |
| Backup/restore drill | Остановить сервер; скопировать закрытую SQLite DB в приватный backup; восстановить копию в отдельный приватный каталог и запустить отдельный loopback port | Jobs/reports сохранились, audit verify успешен, штатные identities работают; сохранить timestamp и head audit без tokens |
| Crash/restart на host | В отдельной тестовой базе запустить synthetic job; аварийно остановить только принадлежащий тесту process, затем перезапустить с той же DB | Interrupted queued/running становятся failed и не replay; flock не допускает второй процесс; контейнеры не остаются работающими |
| Ручной retention | В тестовой базе администратор запускает prune согласно API.md/OPERATIONS.md | Устаревший report очищен; metadata/audit сохранены; расписание автоматической очистки отсутствует |
| Локальная нагрузка/ресурсы | На disposable tenant повторить bounded synthetic submits до quota и наблюдать CPU/RAM/container cleanup | 429 при лимите; cancel/timeout освобождает worker; измерить host-specific latency/RAM, не объявлять production SLA |

Для backup остановка обязательна: не копируйте работающую DB простым cp и не удаляйте lock чужого процесса. Восстановление тестируйте на копии, не поверх активной базы. Backups содержат token hashes и отчёты; им нужны те же приватные права. Hash-chain сравнивайте с отдельно сохранённым доверенным head; полная перепись DB владельцем хоста остаётся угрозой.

## Как записывать результаты

Для каждого пункта зафиксируйте: release tag/commit, дату, ОС/runtime/daemon версии, команду или действие, exit code, passed/failed/not-run и ссылку на очищенное evidence. Не включайте tokens, Authorization headers, персональные адреса, реальные telemetry или полные env dumps. При failure приложите безопасное минимальное synthetic воспроизведение. До выполнения запись остаётся not-run; CI success не заменяет её.

## Внешняя инфраструктура

Public hosting, TLS/IdP/MFA, отдельные tenant VM/runtime, внешний append-only audit, scheduled retention, независимый security audit и production load test отсутствуют. Их нельзя проверить на текущей локальной реализации и нельзя считать passed. Критерии готовности перечислены в ROADMAP.md; развёртывание требует отдельно предоставленной инфраструктуры и пересмотра модели угроз.
