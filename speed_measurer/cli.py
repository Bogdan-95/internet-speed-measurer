"""CLI-интерфейс для speed_measurer."""

import argparse
import sys

from .config import REQUESTS_COUNT, VERSION
from .core import RequestResult, run_speed_test
from .exceptions import InvalidURLError
from .report import print_report

# ── ANSI-цвета (без внешних зависимостей) ──────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Парсит аргументы командной строки.

    Args:
        args: Аргументы для парсинга (для тестирования).

    Returns:
        Спарсенные аргументы.
    """
    parser = argparse.ArgumentParser(
        prog="speed_measurer",
        description="Утилита для замера скорости интернет-соединения.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры запуска:
  python -m speed_measurer https://example.com/image.jpg
  python -m speed_measurer -c 5     "https://speed.cloudflare.com/__down?bytes=10000000"
  python -m speed_measurer          # интерактивный ввод URL
    """,
    )

    parser.add_argument(
        "url",
        nargs="?",
        default=None,
        help="URL для замера скорости",
    )

    parser.add_argument(
        "-c",
        "--count",
        type=int,
        default=REQUESTS_COUNT,
        dest="count",
        help=f"Количество запросов (по умолчанию: {REQUESTS_COUNT})",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    return parser.parse_args(args)


def get_url_interactive() -> str:
    """Запрашивает URL у пользователя интерактивно.

    Returns:
        Введённый URL.

    Raises:
        InvalidURLError: Если пользователь ввёл пустую строку.
    """
    print("Введите URL для замера скорости:")
    print("(например: https://example.com/image.jpg)")
    print()

    url = input("URL: ").strip()

    if not url:
        raise InvalidURLError("URL не может быть пустым")

    return url


def _print_progress(current: int, total: int, result: RequestResult) -> None:
    """Печатает строку прогресса для одного запроса.

    Args:
        current: Номер текущего запроса (1-based).
        total: Всего запросов.
        result: Результат запроса.
    """
    bar_width = 20
    filled = int(bar_width * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_width - filled)

    if result.success:
        mb = result.bytes_downloaded / 1_000_000
        status = f"{GREEN}✓{RESET}"
        details = f"{mb:8.3f} МБ за {result.elapsed_time:6.3f} сек"
    else:
        status = f"{RED}✗{RESET}"
        details = result.error_message or "ошибка"

    print(f"  [{bar}] {current:>2}/{total} {status}  {details}")


def main(args: list[str] | None = None) -> int:
    """Главная функция CLI.

    Args:
        args: Аргументы командной строки (для тестирования).

    Returns:
        Код завершения: 0 — успех, 1 — ошибка.
    """
    try:
        parsed = parse_args(args)

        if parsed.count <= 0:
            print(
                f"Ошибка: количество запросов должно быть > 0 "
                f"(получено {parsed.count})",
                file=sys.stderr,
            )
            return 1

        url = parsed.url if parsed.url else get_url_interactive()

        print(f"\nЗапуск замера скорости: {url}")
        print(f"Количество запросов:    {parsed.count}")
        print("-" * 60)

        results = run_speed_test(
            url,
            count=parsed.count,
            progress_callback=_print_progress,
        )

        success = print_report(results)

        return 0 if success else 1

    except InvalidURLError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\n\nЗамер прерван пользователем (Ctrl+C).")
        return 1

    except Exception as e:  # noqa: BLE001
        print(f"Неожиданная ошибка: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
