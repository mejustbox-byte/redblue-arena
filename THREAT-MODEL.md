# Threat model

## Scope и доверие

Версия 0.2.0: офлайн CLI и локальный control plane на доверенном POSIX host. Активы: identity tokens, tenant scope, jobs/reports, runtime, database/audit. Облачный публичный сервис пока не развёрнут.

Недоверенные границы: HTTP config/body/token, JSON CLI, target и scenario strings. Доверенные компоненты: проверенный Python-код, runtime, SQLite host, provision operator, Docker daemon и локальный образ. Загрузка внешних модулей отсутствует. Principal внутренней Python API не заменяет authentication.

| Угроза | Реализованный контроль | Остаточный риск |
| --- | --- | --- |
| Scope expansion | Server-owned tenant allowlist, authorized и scope_confirmed, повторная worker validate | Юридическая авторизация декларативная |
| Межарендаторный доступ | Tenant из токена, tenant predicates на jobs/audit, RBAC tests | Владелец хоста может читать SQLite |
| Несанкционированный submit/cancel/prune | Bearer roles; analyst cancel только своё задание, admin scoped | Нет внешнего IdP/MFA, токен даёт права до revoke |
| Инъекция команд/модулей | Fixed registries и argv без shell, JSON неизвестные поля отклоняются | Доверенный maintainer может изменить код |
| Worker network/filesystem | Docker network none, read-only, non-root, caps dropped, no mounts | Docker не заменяет отдельную VM от privileged-host угроз |
| Отсутствующий sandbox | Docker default fail-closed | trusted-local явно не изолирован |
| DoS | Payload/event/report/time/CPU/memory/PID limits, active/daily/storage/rate caps | Локальный host может нарушить лимиты; global rate может блокировать других |
| Browser CSRF/DNS rebinding/XSS | Exact Host/Origin, bearer, no CORS, CSP, textContent, no token query/localStorage | Browser extension/host compromise остаются вне модели |
| Утечка секретов | Token hash в DB, очистка worker env, нет access logs; приватные файлы/игнорирование git | Provision stdout/token file и память браузера чувствительны |
| Подмена audit | Tenant hash-chain, verify endpoint, audit denial/lifecycle, bounded capacity | Переписывание всей DB или удаление хвоста без внешнего head не обнаруживается |
| Рестарт/replay | flock, interrupted jobs failed и audit, без auto replay | Host должен хранить backup вне общей failure domain |
| Supply chain | Нет runtime зависимостей, pinned Ruff; локальный container pull=never | Базовый Docker tag изменяемый, digest ещё не закреплён |

## Ретенция и приватность

Отчёты только синтетические. Admin prune очищает report старше retention_days; metadata/audit сохраняются. Срок не исполняется автоматически до вызова prune. Неаутентифицированные запросы не записываются в tenant audit, и полные URL/тела/token не логируются. Для аудит-доказательств нужны независимые backups/head.

## Недопустимые расширения

Не добавляйте real credentials, production telemetry, arbitrary commands, network targets, exploit payloads или непроверенную plugin загрузку. Не публикуйте loopback service через tunnel или proxy. Настройка public hosting, TLS, IdP, tenant runtime isolation и audit sink требует пересмотра этой модели и отдельной проверки инфраструктуры.

SECURITY.md описывает reporting. Старый docs/THREAT_MODEL.md сохранён как историческая ссылка; актуальный документ — этот.

## Проверка версии

Контракты относятся к локальной версии 0.2.0. Подготовка и проверка checkout: `python3.12 scripts/dev.py setup`, затем `python3.12 scripts/dev.py check --docker` на POSIX с работающим Docker. Статус evidence и Cloud snapshot — [VERIFICATION.md](VERIFICATION.md); public hosting остаётся в [ROADMAP.md](ROADMAP.md).
