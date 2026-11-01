# Internet Speed Measurer

CLI-утилита для измерения скорости загрузки данных через HTTP.

Программа выполняет серию последовательных запросов, измеряет продолжительность скачивания и рассчитывает суммарную пропускную способность.

Проект реализован исключительно на стандартной библиотеке Python.

## Возможности

- Измерение скорости скачивания по URL.
- Настройка количества запросов.
- Потоковое чтение HTTP-ответов чанками по 64 KB.
- Отображение прогресса выполнения.
- Подсчёт среднего времени и общей скорости.
- Обработка сетевых ошибок и таймаутов.
- Интерактивный ввод URL.
- Unit-тесты с использованием Mock без реальных сетевых запросов.

## Технологический стек

- Python 3.10+
- urllib
- argparse
- unittest
- unittest.mock

Внешние Python-зависимости не требуются.

## Установка

```bash
git clone https://github.com/Bogdan-95/internet-speed-measurer.git
cd internet-speed-measurer
```

Создание виртуального окружения:

```bash
python -m venv .venv
source .venv/bin/activate
```

## Использование

Измерение скорости:

```bash
python -m speed_measurer https://example.com/file.bin
```

Изменение количества запросов:

```bash
python -m speed_measurer -c 5 https://example.com/file.bin
```

Справка:

```bash
python -m speed_measurer --help
```

## Как рассчитывается скорость

Используется суммарный объём успешно загруженных данных, разделённый на суммарное время успешных запросов.

```text
speed = total_downloaded_bytes / total_elapsed_time
```

В расчётах применяются десятичные мегабайты:

```text
1 MB = 1,000,000 bytes
```

## Тестирование

Тесты запускаются без обращения к реальным внешним серверам.

```bash
python -m unittest discover tests -v
```

Проверяются:

- валидация URL;
- потоковое чтение;
- обработка HTTP-ошибок;
- обработка таймаутов;
- сбор результатов;
- callback прогресса;
- CLI.

## Структура

```text
speed_measurer/
├── __main__.py
├── cli.py
├── config.py
├── core.py
├── exceptions.py
└── report.py

tests/
├── test_cli.py
├── test_core.py
└── test_report.py
```

## Ограничения

Утилита измеряет только скорость скачивания. Она не измеряет upload, ping или jitter.

Результат зависит от сервера, маршрута, VPN, прокси и текущей сетевой нагрузки.

## Автор

Bogdan Rengo

GitHub: https://github.com/Bogdan-95
