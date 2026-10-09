# Operations — local laboratory

## Граница эксплуатации

Версия 0.2.0 предназначена для одного доверенного host и локальной лаборатории. Поддерживаются Linux/macOS, Python 3.12, стандартная SQLite. Один процесс обслуживает базу; POSIX flock предотвращает двойной запуск и повторное provision во время serve. Root/владелец хоста остаётся доверенным. Docker daemon — привилегированный компонент; socket никогда не монтируется в worker.

## Workers и ресурсы

Docker runner запускает только фиксированную команду redblue_arena.worker в локальном образе redblue-arena:lab. Политика: pull=never, network=none, read-only, cap-drop ALL, no-new-privileges, UID/GID 65532, 32 PID, 128 MiB, 0.5 CPU, stdin JSON. Нет host mounts, портов, arbitrary commands или secret injection. Worker имеет timeout 10 секунд, ограничение отчёта 2 MiB. Контейнер удаляется после завершения, отмены и timeout.

Trusted-local runner запускает тот же встроенный worker subprocess с очищенным окружением. Это отдельный явно выбранный режим для доверенного кода, без гарантии сетевой или файловой изоляции. Не используйте его для внешних участников.

Control plane: 2 worker threads, глобально до 16 active заданий, до 2 active и 100 заданий/24 часа на tenant, до 1000 сохранённых metadata-записей на tenant. Квоты атомарно проверяются SQLite BEGIN IMMEDIATE. HTTP: до 16 handler threads, 5 секунд socket timeout, 120 запросов/мин глобально. Host provisioning доверенное; произвольная self-registration отсутствует.

## Токены, роли и scope

Provision выполняется только trusted host CLI, не через API. Токены имеют 256 бит случайности; SQLite хранит SHA-256 hash. Токен показывается один раз. UI держит его в памяти; logout очищает память и пользовательские данные интерфейса. Не публикуйте .token, базу или backup.

Роли: viewer читает задания своего tenant; analyst создаёт и отменяет собственные задания; admin также читает audit и вызывает retention. Ни одна роль не пересекает tenant. Scope задаётся при provision; повторный provision требует точного совпадения списка целей. Изменение scope требует отдельной проверенной миграции; hidden scope expansion не поддерживается.

Для отзыва остановите сервер, введите токен через безопасный prompt вне history и вызовите revoke:

```bash
read -r -s REDBLUE_TOKEN
export REDBLUE_TOKEN
python -m redblue_arena.web --db .lab/arena.sqlite revoke
unset REDBLUE_TOKEN
```

Это команда trusted host, не remote API. Возобновите сервер после отзыва. Токены уже созданных заданий не заменяют policy: config проверяется перед worker execution.

## Retention, аудит, backup

По умолчанию срок отчётов 7 дней (serve --retention-days 1–365). Очистка выполняется admin через dashboard или POST /api/retention/prune. Удаляется только report у завершённых заданий старше срока; metadata и audit остаются. Отказы, provision/revoke, очередь, выполнение, отмена, рестарт и retention отражаются в аудитe. Неаутентифицированные HTTP отказы не содержат доверенного tenant и не пишутся в его audit.

Hash-chain проверяется через GET /api/audit; каждый tenant имеет отдельные sequence и head. Chain обнаруживает локальное повреждение/изменение записей, но не переписывание всей базы владельцем хоста. Для независимого доказательства сохраняйте head и backups в отдельно управляемом хранилище; этого внешнего хранилища в проекте нет.

Лимит audit: 100000 записей/tenant, после чего операции закрываются отказом. При достижении capacity остановите сервер, архивируйте базу, проверьте chain и создайте новую лабораторную базу. Не удаляйте отдельные audit rows и не сбрасывайте head внутри рабочей базы.

Backup: остановите serve, скопируйте SQLite и приватно сохраните вместе с временем, версией кода и audit head. Восстановление: закрытый host, права 0600, запуск совместимой версии; interrupted jobs не replay. Статус stale reports не является real-time monitoring.

## Перед внешним cloud deployment


## Проверка версии


Приёмка пользовательского host не подтверждена CI: [LOCAL-INFRA-CHECKS.md](LOCAL-INFRA-CHECKS.md) содержит команды, критерии и not-run статус. В 0.2.1 эксплуатационное поведение платформы не меняется.
