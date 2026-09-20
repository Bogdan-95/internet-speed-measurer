"""Сетевая логика для замера скорости."""

import time
from collections.abc import Callable
from dataclasses import dataclass
from urllib import request
from urllib.error import HTTPError, URLError

from .config import REQUESTS_COUNT, TIMEOUT
from .exceptions import InvalidURLError

# Размер чанка при потоковом чтении ответа (64 КиБ)
CHUNK_SIZE = 64 * 1024


@dataclass
class RequestResult:
    """Результат одного HTTP-запроса."""

    success: bool
    bytes_downloaded: int
    elapsed_time: float
    error_message: str | None = None


# Тип callback-функции для отображения прогресса
ProgressCallback = Callable[[int, int, "RequestResult"], None]


def _validate_url(url: str) -> None:
    """Проверяет корректность URL.

    Args:
        url: URL для проверки.

    Raises:
        InvalidURLError: Если URL некорректен.
    """
    if not url or not url.strip():
        raise InvalidURLError("URL не может быть пустым")

    if not url.strip().lower().startswith(("http://", "https://")):
        raise InvalidURLError("URL должен начинаться с http:// или https://")


def measure_single_request(url: str) -> RequestResult:
    """Выполняет один HTTP-запрос и замеряет скорость.

    Ответ читается потоково (чанками), без загрузки целиком в память.

    Args:
        url: URL для загрузки.

    Returns:
        RequestResult с результатами запроса.

    Raises:
        InvalidURLError: Если URL некорректен.
    """
    _validate_url(url)

    start_time = time.monotonic()

    try:
        req = request.Request(
            url,
            headers={"User-Agent": "SpeedMeasurer/1.0"},
        )

        total_bytes = 0
        with request.urlopen(req, timeout=TIMEOUT) as response:
            # Потоковое чтение чанками — защита от MemoryError
            while True:
                chunk = response.read(CHUNK_SIZE)
                if not chunk:
                    break
                total_bytes += len(chunk)

        elapsed = time.monotonic() - start_time

        return RequestResult(
            success=True,
            bytes_downloaded=total_bytes,
            elapsed_time=elapsed,
        )

    except HTTPError as e:
        # HTTPError — наследник URLError, поэтому обрабатываем раньше
        return RequestResult(
            success=False,
            bytes_downloaded=0,
            elapsed_time=0.0,
            error_message=f"HTTP {e.code}: {e.reason}",
        )
    except URLError as e:
        reason = getattr(e, "reason", e)
        return RequestResult(
            success=False,
            bytes_downloaded=0,
            elapsed_time=0.0,
            error_message=f"Сетевая ошибка: {reason}",
        )
    except TimeoutError:
        return RequestResult(
            success=False,
            bytes_downloaded=0,
            elapsed_time=0.0,
            error_message=f"Таймаут ({TIMEOUT} сек)",
        )
    except OSError as e:
        return RequestResult(
            success=False,
            bytes_downloaded=0,
            elapsed_time=0.0,
            error_message=f"Ошибка ввода-вывода: {e}",
        )


def run_speed_test(
    url: str,
    count: int = REQUESTS_COUNT,
    progress_callback: ProgressCallback | None = None,
) -> list[RequestResult]:
    """Запускает серию последовательных запросов для замера скорости.

    Args:
        url: URL для загрузки.
        count: Количество запросов.
        progress_callback: Необязательная функция для отображения прогресса.
            Вызывается после каждого запроса с аргументами
            (номер_запроса, всего_запросов, результат).

    Returns:
        Список результатов для каждого запроса.

    Raises:
        InvalidURLError: Если URL некорректен.
    """
    _validate_url(url)

    results: list[RequestResult] = []

    for i in range(count):
        result = measure_single_request(url)
        results.append(result)

        if progress_callback is not None:
            progress_callback(i + 1, count, result)

    return results
