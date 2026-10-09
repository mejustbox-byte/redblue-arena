# Roadmap

## Выполнено — офлайн MVP

- [x] Явная авторизация, allowlist, bounded synthetic telemetry, JSON report и CLI audit.
- [x] Положительные/отрицательные fixtures на пороге и ниже, target isolation.
- [x] GitHub Actions lint, format, unit и CLI smoke checks.
- [x] Отдельная опубликованная Codex Cloud среда для redblue-arena; базовый commit 3658104 восстановлен и проверен без secrets.

## Реализовано — локальная версия 0.2.0

- [x] Версионируемые правила, inclusive временные окна, configurable thresholds.
- [x] Labelled synthetic evaluation, confusion matrix, FP rate/recall с оговоркой о synthetic-only данных.
- [x] Отдельные modules packages, API v2 и documented migration/schema contracts.
- [x] Фиксированные Docker workers с network none, non-root, read-only и ресурсными лимитами; отдельный integration CI job.
- [x] Tenant-scoped token auth/RBAC, scope confirmation, quotas, cancellation/timeout.
- [x] Постоянные SQLite jobs/audit, hash-chain verify, report retention, single-owner lock и restart без replay.
- [x] Локальные dashboard и JSON API после негативных tenant/RBAC/scope/HTTP тестов.
- [x] Operations, API, module extension guide, installation и обновлённая модель угроз.

## Инфраструктура и публичное облако — не выполнено

- [x] Codex Cloud snapshot обновлён на 0.2.0 commit 2f9b651 и восстановлен в новой задаче; результаты в VERIFICATION.md. Snapshot подтверждает код платформы до финальных изменений документации и dev tooling.
- [ ] Выбрать cloud provider и deployment account, TLS, external IdP/MFA и production server.
- [ ] Отдельные runtime/VM boundaries для tenant, ingress/egress policies вне приложения.
- [ ] Независимый append-only audit sink, backup/restore drill и automatic retention scheduler.
- [ ] Независимые security tests, нагрузочные тесты и эксплуатационное согласование перед публичным доступом.
- [ ] Закрепить digest проверенного базового container image для production-воспроизводимости.

## Среда разработки и выпуск

- [x] Repository-owned setup/check/doctor, закреплённая dev-зависимость и единый CI gate.
- [x] Документация согласована с локальной версией 0.2.0; LICENSE сохранена.
- [x] v0.2.0 опубликован после CI на main (run 37889685520): source tag/release на commit 89d0d90; будущие версии требуют отдельного решения.

Real integrations, arbitrary commands и непроверенные plugins не входят в безопасную лабораторную реализацию. Наличие локальной платформы/CI не подтверждает production public-cloud readiness. Слияние и выпуск разрешены владельцем после проверок; планы не обозначаются как работающие гарантии.

## Проверяемость 0.2.1

- [x] Assets gate: локальные Markdown-ссылки и dashboard JS syntax.
- [x] Команды и критерии ручной приёмки оформлены в LOCAL-INFRA-CHECKS.md с not-run статусами.
- [ ] Приёмка конкретного пользовательского host: browser E2E, Docker daemon, права, restore/crash/load evidence.
