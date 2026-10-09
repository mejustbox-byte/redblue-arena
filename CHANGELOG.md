# Changelog

## Unreleased — 0.2.0

- Подтверждены успешные unit/HTTP/CLI проверки, Docker build и оба Docker integration tests в GitHub Actions; обновлённый Codex Cloud snapshot опубликован и восстановлен на code commit 2f9b651.

- Модульный API v2, report schema v2, относительные timestamps, versioned configurable sliding-window rule.
- Добавлены spread-logins и labelled fixture evaluation с confusion matrix, recall и false positive rate.
- Реализован локальный SQLite control plane: hashed tokens, tenant-scoped RBAC/scope, квоты, очередь, cancel/timeout, restart без replay.
- Добавлены Docker runner (network none, non-root, read-only, resource caps) и явно доверенный trusted-local режим без sandbox.
- Реализованы tenant hash-chain audit, проверка целостности, report retention и single-owner database lock.
- Добавлены loopback API/dashboard, Host/Origin/CSP guards, bounded requests и Docker integration job в CI.
- Обновлены архитектура, модель угроз, установка, API, module migration и operations; публичное cloud hosting остаётся отдельным этапом.

- Добавлены сценарии `threshold-logins` и `benign-logins`, примеры конфигураций и регрессионная матрица detection quality.
- Проверены успешные входы, разделение целей, порог и обязательная авторизация новых сценариев.
- Codex Cloud опубликована; восстановление и smoke test базового commit 3658104 подтверждены в новой задаче.

- Зафиксирован стек Python 3.12, pip/venv, unittest, Ruff, Docker и GitHub Actions.
- Добавлены CLI smoke test и конфигурации dev-инструментов, контейнера и CI; GitHub Actions CI прошёл успешно, проверка базовой облачной среды завершена.

- Расширены архитектура Red/Blue, модель угроз, безопасные границы и contribution guide.
- Добавлены сценарии использования, конфигурация лаборатории, диагностика и критерии готовности roadmap.

## 0.1.0 — 2026-10-09

- Добавлен исполняемый офлайн MVP без сторонних зависимостей.
- Добавлены контракты модулей, синтетический сценарий неудачных входов и правило обнаружения.
- Реализованы строгая конфигурация, явная авторизация, allowlist и JSON audit log.
- Добавлены тесты, пример конфигурации и модель угроз.
- README и INSTALL содержат воспроизводимые команды; ROADMAP отделяет готовые функции от планов.

## Начальная документация

- Добавлены MIT LICENSE, SECURITY и базовые архитектурные документы.
