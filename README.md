# RedBlue Arena

Публичный проект модульной безопасной эмуляции и проверки обнаружения для авторизованных лабораторий. MIT [LICENSE](LICENSE).

## Реализовано в 0.2.0

- Четыре детерминированных синтетических сценария, строгий scope и явная авторизация.
- Правило `auth.repeated_failures` v2: настраиваемый порог и временное окно.
- Оценка control fixtures: confusion matrix, recall и false positive rate.
- Отдельный API модулей v2 без загрузки произвольного кода.
- Локальный control plane: bearer-токены, tenant-scoped RBAC, SQLite, квоты, очередь, отмена и timeout.
- Непривилегированные Docker workers без сети, capabilities и записи в root filesystem.
- Постоянный tenant-scoped hash-chain аудит, проверка целостности и очистка устаревших отчётов.
- Dashboard и JSON API только на `127.0.0.1` с проверкой Host/Origin, без CORS.

Это исполняемая локальная лабораторная платформа. Публичный облачный сервис пока не развёрнут: TLS, внешний identity provider, отдельный runtime для арендаторов и эксплуатационная проверка требуют инфраструктуры. Codex Cloud — среда разработки, а не hosting платформы.

## Быстрый офлайн запуск

Требуется Python 3.12.x; runtime использует только стандартную библиотеку.

```bash
python -m redblue_arena --config examples/lab.json
python -m redblue_arena --config examples/lab.json --evaluate
python -m unittest discover -s tests -v
python tests/smoke.py
```

| Сценарий | Конфигурация | События | Ожидаемые findings с правилом по умолчанию |
| --- | --- | --- | --- |
| failed-logins | examples/lab.json | 6 ошибок за 5 секунд | 1 |
| threshold-logins | examples/threshold.json | 5 ошибок за 4 секунды | 1 |
| benign-logins | examples/benign.json | 4 ошибки, 2 успеха | 0 |
| spread-logins | examples/spread.json | 6 ошибок с интервалом 61 секунда | 0 |

Время вымышленное и относительно начала задания. Генераторы ничего не ждут и не выполняют попытки входа. `lab://training` — логический идентификатор, а не адрес.

Для dashboard, provision, запуска workers и API см. [INSTALL.md](INSTALL.md) и [API.md](API.md). Для модулей и миграции JSON schema v1 → v2 см. [MODULE-API.md](MODULE-API.md).

## Безопасность и ограничения

`authorized: true` и `scope_confirmed: true` — декларации оператора, а не юридическая проверка. В HTTP API роль, tenant scope и квоты проверяются сервером. Каждый worker повторно валидирует конфигурацию. Реальные эксплойты, команды, сетевые адреса и непроверенные плагины не принимаются.

Docker — режим по умолчанию; его отсутствие вызывает отказ. `trusted-local` разрешён только для доверенных встроенных модулей на собственном компьютере: subprocess не является sandbox. SQLite и hash-chain не защищают от владельца хоста, способного переписать всю базу. Токены не сохраняются в репозитории или localStorage.

См. [SECURITY.md](SECURITY.md), [THREAT-MODEL.md](THREAT-MODEL.md), [ARCHITECTURE.md](ARCHITECTURE.md), [TECH-STACK.md](TECH-STACK.md), [ROADMAP.md](ROADMAP.md), [CHANGELOG.md](CHANGELOG.md), [CONTRIBUTING.md](CONTRIBUTING.md), [OPERATIONS.md](OPERATIONS.md).

Проверенные результаты code commit 0.2.0: [VERIFICATION.md](VERIFICATION.md).
