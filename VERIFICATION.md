# Verification — 2026-10-09

## Проверенный код

Repository: mejustbox-byte/redblue-arena. Code commit: `2f9b65104ca68d1c9595489a8d1e5798dd77d376`, branch `codex/local-platform`, PR #3. Следующий documentation-only commit содержит эту запись; Cloud snapshot закреплён на указанном code commit и не обновляется по каждому documentation-only изменению.

| Проверка | Результат | Где |
| --- | --- | --- |
| Python/runtime | 3.12.14, pip check OK, Ruff 0.15.0 | Local и Codex Cloud |
| Ruff lint/format | OK, 20 Python files | Local, CI, Codex Cloud |
| unittest default suite | 29 discovered, 27 passed, 2 Docker skipped | Local и restored Codex Cloud |
| CLI smoke | 4 сценария, report schema 2 | Local, CI, restored Cloud |
| Fixture evaluation | TP2, TN2, FP0, FN0 | Local, restored Cloud |
| Docker build | success | CI run 37887959962 |
| Real Docker worker | success | CI docker job, test_container_worker |
| Non-root/read-only/network boundary | success | CI docker job, test_runtime_boundaries |
| HTTP/RBAC/tenant/quota/cancel/audit tests | passed | Local, CI, restored Cloud |
| Documentation links / JS syntax | OK | Local |
| Typical tracked secret indicators | 46 files, 0 matches | Restored Cloud |
| Git status | Clean before/after, HEAD unchanged | Restored Cloud |

CI: [Lab checks run](https://github.com/mejustbox-byte/redblue-arena/actions/runs/37887959962). Jobs `test` (113682110373) и `docker` (113682110660) completed/success. Docker opt-in job запускает 5 test_runner checks, включая 2 реальные контейнерные проверки; это не просто наличие Dockerfile.

## Среда разработки

Codex Cloud `redblue-arena`: единственный репозиторий mejustbox-byte/redblue-arena, доступ «Только я», без secrets/переменных/дополнительных доменов. Сеть ограничена preset менеджеров пакетов; это не утверждение полного OS deny-egress для всей development среды. Worker deny-egress реализован отдельно Docker network=none.

Snapshot опубликован на code commit выше, detached HEAD допустим. Новая независимая задача восстановила сохранённую .venv и прошла тесты. HTTP tests потребовали разрешения loopback sockets; они используют временные базы/токены с cleanup. Постоянные токены, базы или сервисы не создавались. CLAUDE.md не читался. Docker не запускался в restored Cloud: его evidence получено отдельно в CI.

## Ограничения evidence

Это проверка локальной лабораторной версии 0.2.0. Нет public cloud deployment, TLS/IdP, independent immutable audit sink, VM-level adversarial tenant isolation, production load test или независимого security audit. Secret regex scan не доказывает отсутствие всех возможных секретов. Ноль FP на четырёх control fixtures не оценивает detection efficacy на реальном трафике. Публикация разрешена владельцем после успешного CI. Финальный dev tooling и документация проверяются отдельным PR/main run; источник конкретного релиза — тег v0.2.0.

## Финальная среда разработки

scripts/dev.py check прошёл локально: pip check, lint/format (21 Python files), 27 passed/2 Docker skipped, 4 smoke fixtures, evaluation TP2/TN2/FP0/FN0. Setup проверен в новом временном checkout/venv и повторно в том же окружении; постоянные lab data не создаются. CI использует тот же setup; release job разрешён только на push main после успешных test и docker jobs, только для 0.2.0 и без перезаписи существующего выпуска. Секрет GITHUB_TOKEN предоставляется Actions во время job, не хранится в проекте. Финальный результат CI/релиза проверяется через GitHub; прежний Cloud snapshot не объявляется обновлённым этим workflow.

## Опубликованный выпуск

2026-10-09 PR #3 слит в main: `89d0d903be047c89782b698f448c9ff59dfa3712`. [Итоговый CI run 37889685520](https://github.com/mejustbox-byte/redblue-arena/actions/runs/37889685520) завершился success: test, docker и release. PR gate [37889615160](https://github.com/mejustbox-byte/redblue-arena/actions/runs/37889615160) также прошёл перед слиянием.

[GitHub Release v0.2.0](https://github.com/mejustbox-byte/redblue-arena/releases/tag/v0.2.0) опубликован, draft=false, prerelease=false; lightweight tag указывает точно на commit выше. Доступны стандартные source archives GitHub, дополнительных binary/container assets нет. PR #1 включён через историю объединённого PR; PR #2 закрыт как superseded, его изменения присутствуют в main. Эта финальная запись изменяет только документацию; release tag и code не перезаписываются. Codex Cloud snapshot остаётся на 2f9b651, как описано выше.
