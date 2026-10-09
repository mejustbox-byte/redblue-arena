# Roadmap

## Выполнено — офлайн MVP

- [x] Явная авторизация, allowlist, bounded synthetic telemetry, JSON report и CLI audit.
- [x] Положительные/отрицательные fixtures на пороге и ниже, target isolation.
- [x] GitHub Actions lint, format, unit и CLI smoke checks.
- [x] Отдельная опубликованная Codex Cloud среда для redblue-arena; базовый commit 3658104 восстановлен и проверен без secrets.

## Реализовано — версия 0.2.0 в PR

- [x] Версионируемые правила, inclusive временные окна, configurable thresholds.
- [x] Labelled synthetic evaluation, confusion matrix, FP rate/recall с оговоркой о synthetic-only данных.
- [x] Отдельные modules packages, API v2 и documented migration/schema contracts.
- [x] Фиксированные Docker workers с network none, non-root, read-only и ресурсными лимитами; отдельный integration CI job.
- [x] Tenant-scoped token auth/RBAC, scope confirmation, quotas, cancellation/timeout.
- [x] Постоянные SQLite jobs/audit, hash-chain verify, report retention, single-owner lock и restart без replay.
- [x] Локальные dashboard и JSON API после негативных tenant/RBAC/scope/HTTP тестов.
- [x] Operations, API, module extension guide, installation и обновлённая модель угроз.

## Инфраструктура и публичное облако — не выполнено

- [ ] Обновить и повторно проверить Codex Cloud snapshot на 0.2.0 после review/выбора commit.
- [ ] Выбрать cloud provider и deployment account, TLS, external IdP/MFA и production server.
- [ ] Отдельные runtime/VM boundaries для tenant, ingress/egress policies вне приложения.
- [ ] Независимый append-only audit sink, backup/restore drill и automatic retention scheduler.
- [ ] Независимые security tests, нагрузочные тесты и эксплуатационное согласование перед публичным доступом.
- [ ] Закрепить digest проверенного базового container image и release artifacts.

Real integrations, arbitrary commands и непроверенные plugins не входят в безопасную лабораторную реализацию. Наличие локальной платформы/CI не подтверждает production public-cloud readiness. PR остаются draft до review; планы не обозначаются как работающие гарантии.
