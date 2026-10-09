# Local API v1

База: `http://127.0.0.1:8765`. Host должен точно совпадать с адресом и портом; при наличии Origin он должен совпадать с базой. Внешний CORS запрещён. API использует `Authorization: Bearer <token>`, токен выдаётся только trusted-host provision. POST: Content-Type application/json, Content-Length, тело до 64 KiB; chunked encoding не принимается.

| Метод | Путь | Доступ | Назначение |
| --- | --- | --- | --- |
| GET | /health | Без токена | Liveness и runner mode, без пользовательских данных |
| GET | / | Без токена | Статический dashboard |
| GET | /app.js | Без токена | Статический JS |
| GET | /api/me | Любая роль | Tenant, subject, role, runner |
| GET | /api/jobs | Любая роль | Последние 100 заданий текущего tenant |
| GET | /api/jobs/{id} | Любая роль текущего tenant | Конфигурация, статус и отчёт |
| POST | /api/jobs | admin, analyst | Создать задание с config и scope_confirmed=true |
| POST | /api/jobs/{id}/cancel | admin или создавший analyst | Отмена queued/running; тело {} |
| GET | /api/audit | admin текущего tenant | Проверенная hash-chain и её head |
| POST | /api/retention/prune | admin текущего tenant | Очистить старые отчёты; тело {} |

Tenant никогда не принимается из JSON или URL: его определяет аутентифицированный токен. Admin не является глобальным администратором — права ограничены его tenant. Аналитик видит все отчёты своего tenant; если нужны персональные приватные отчёты, выделите отдельный tenant.

Пример тела POST /api/jobs:

```json
{
  "scope_confirmed": true,
  "config": {
    "authorized": true,
    "allowed_targets": ["lab://training"],
    "target": "lab://training",
    "scenario": "failed-logins"
  }
}
```

Ответ 202: job_id. Состояния: queued → running → completed/failed/cancelled. После рестарта queued/running становятся failed с audit job.interrupted; задания автоматически не повторяются. Отмена идемпотентна для завершённого доступного задания и не меняет его результат. Worker cancellation может занять до 5 секунд на очистку Docker; статус cancel_requested не означает мгновенного завершения процесса.

403: authentication/role/scope/job access denied; 400: invalid body/config; 429: квота или rate limit; 404: неизвестный endpoint; 500: общая ошибка без внутренних подробностей. CORS не разрешается, токены не передаются в query string, access logs отключены. Клиент обновляет список вручную, без polling.

Python ControlPlane API — доверенная внутренняя библиотека: Principal создаётся после authenticate сервером. Переданный вручную Principal не является самостоятельным доказательством identity.

## Проверка версии

Контракты относятся к локальной версии 0.2.0. Подготовка и проверка checkout: `python3.12 scripts/dev.py setup`, затем `python3.12 scripts/dev.py check --docker` на POSIX с работающим Docker. Статус evidence и Cloud snapshot — [VERIFICATION.md](VERIFICATION.md); public hosting остаётся в [ROADMAP.md](ROADMAP.md).
