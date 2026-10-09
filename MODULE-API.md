# Module API v2

Контракты: `redblue_arena.modules.contracts`. Реестр: `modules.scenarios.SCENARIOS`. API_VERSION = 2. Нет entrypoint discovery, импорта путей из JSON или remote plugin loading.

`Scenario.generate(target) -> list[Event]`: 1–10000 синтетических событий. Поля Event: sequence (целое, непрерывно с 1), target, kind=authentication, outcome=failure/success, synthetic=true, timestamp_ms (целое, 0–86400000). Время не убывает; одинаковые timestamps допускаются. Нормализация отвергает boolean в числовых полях.

`Detector.detect(events) -> list[dict]`: работает с нормализованной телеметрией. Правило RepeatedFailures группирует только неудачные authentication события по target; окно включено с обеих сторон. Одна находка на target с максимальным числом ошибок в окне; при равном максимуме сохраняется первое окно. Success не увеличивает счётчик и не сбрасывает его.

Пример встроенного безопасного расширения: `SpreadLogins` в modules/scenarios.py. Новый модуль должен быть проверен, зарегистрирован в коде, документирован и покрыт положительными/отрицательными fixtures. Protocol не является sandbox; доверенный host меняет код только через review.

## Миграция JSON

- Отчёт сценария: schema_version **2** вместо 1.
- Event получает timestamp_ms. Finding получает rule_version, window_ms, window_start_ms, window_end_ms. Отчёт получает конфигурацию rule.
- Старые четырёхполевые config совместимы; отсутствие rule выбирает правило v2 по умолчанию. Старые Python импорты из core сохранены.
- Конструктор Event сохраняет первые пять аргументов; timestamp_ms добавлен последним и по умолчанию 0. Это полезно для старых fixtures, но реальные новые модули задают время явно.
- Потребители, требующие schema_version=1, должны перейти на v2. Нет скрытого down-conversion; изменение окна может изменить detection на разнесённых событиях.

`--evaluate` возвращает отдельную схему evaluation v1: cases, confusion_matrix, recall, false_positive_rate. Четыре контрольных label заданы для правила по умолчанию. Custom rule может изменить качество относительно этих label. Ноль FP на четырёх синтетических fixtures не оценивает production efficacy.

## Проверка версии

