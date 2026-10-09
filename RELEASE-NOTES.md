# RedBlue Arena 0.2.1 — verification and local infrastructure checklist

Поведение локальной платформы и API/report schema v2 сохраняется из 0.2.0. Выпуск добавляет воспроизводимые проверки Markdown-ссылок и dashboard JavaScript syntax в dev setup/CI. Для полного dev gate теперь нужен Node.js; Python runtime по-прежнему не имеет сторонних зависимостей.

Автоматический gate: pip check, Ruff lint/format, 27 default unit/HTTP/worker checks, четыре CLI smoke fixtures, synthetic evaluation и assets verification. Отдельный Docker job строит образ и запускает пять runner checks, включая два реальных container tests. Всего 29 уникальных tests; default suite явно skips два Docker tests. Релиз публикуется только после test/Docker success на итоговом main commit.

```bash
python3.12 scripts/dev.py setup
python3.12 scripts/dev.py check --docker
```

LOCAL-INFRA-CHECKS.md описывает ручную приёмку пользовательского host: Docker daemon, loopback bind, browser E2E/storage, file permissions, backup/restore, crash/restart, retention и нагрузка. Эти пункты не выполнены на пользовательском host и не заменяются CI success. VERIFICATION.md хранит evidence; INSTALL.md — запуск.

Public cloud hosting/TLS/IdP, tenant VM isolation, независимый audit/security/load review остаются вне релиза. Docker base tag изменяемый; hash-chain не защищает от владельца хоста. Source archives предоставляются GitHub, binary/container assets не публикуются. Тег 0.2.0 не перезаписывается. Codex Cloud snapshot 2f9b651 не обновляется этим выпуском.
