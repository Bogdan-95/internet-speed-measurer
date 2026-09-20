"""Расчёт статистики и форматированный вывод результатов."""

from .config import MB
from .core import RequestResult

# ── ANSI-цвета (без внешних зависимостей) ──────────────────────────────
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

# Ширина рамки
WIDTH = 60


def _color_for_speed(speed_mbps: float) -> str:
    """Возвращает ANSI-цвет в зависимости от скорости.

    Args:
        speed_mbps: Скорость в МБ/с.

    Returns:
        ANSI-код цвета.
    """
    if speed_mbps >= 10:
        return GREEN
    if speed_mbps >= 1:
        return YELLOW
    return RED


def calculate_statistics(results: list[RequestResult]) -> dict:
    """Вычисляет статистику по результатам запросов.

    Args:
        results: Список результатов запросов.

    Returns:
        Словарь со статистикой.
    """
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    total_bytes = sum(r.bytes_downloaded for r in successful)
    total_time = sum(r.elapsed_time for r in successful)

    avg_time = total_time / len(successful) if successful else 0.0
    avg_speed_mbps = (total_bytes / MB) / total_time if total_time > 0 else 0.0

    return {
        "total_requests": len(results),
        "successful": len(successful),
        "failed": len(failed),
        "total_bytes": total_bytes,
        "total_time": total_time,
        "avg_time": avg_time,
        "avg_speed_mbps": avg_speed_mbps,
    }


def format_report(results: list[RequestResult]) -> str:
    """Формирует текстовый отчёт о замере скорости.

    Args:
        results: Список результатов запросов.

    Returns:
        Форматированная строка с отчётом.
    """
    stats = calculate_statistics(results)
    speed_color = _color_for_speed(stats["avg_speed_mbps"])

    sep_heavy = "═" * WIDTH
    sep_light = "─" * WIDTH

    lines = [
        "",
        f"{BOLD}{sep_heavy}{RESET}",
        f"{BOLD}  📊  РЕЗУЛЬТАТЫ ЗАМЕРА СКОРОСТИ{RESET}",
        f"{BOLD}{sep_heavy}{RESET}",
        "",
        f"  Всего запросов:      {stats['total_requests']}",
        f"  {GREEN}Успешных:{RESET}            {stats['successful']}",
        f"  {RED}Неуспешных:{RESET}          {stats['failed']}",
        "",
        f"  {DIM}{sep_light}{RESET}",
        "",
        f"  Суммарный объём:     {stats['total_bytes'] / MB:.3f} МБ",
        f"  Общее время:         {stats['total_time']:.2f} сек",
        f"  Среднее время:       {stats['avg_time']:.3f} сек",
        "",
        f"{BOLD}{sep_heavy}{RESET}",
        (
            f"  {BOLD}🚀  СКОРОСТЬ:{RESET}  "
            f"{speed_color}{BOLD}{stats['avg_speed_mbps']:.3f} МБ/сек{RESET}"
        ),
        f"{BOLD}{sep_heavy}{RESET}",
        "",
    ]

    return "\n".join(lines)


def print_report(results: list[RequestResult]) -> bool:
    """Выводит отчёт в консоль.

    Args:
        results: Список результатов запросов.

    Returns:
        True если хотя бы один запрос успешен, False иначе.
    """
    stats = calculate_statistics(results)

    print(format_report(results))

    if stats["successful"] == 0:
        print(f"{RED}ОШИБКА: Все запросы завершились неудачно.{RESET}")
        return False

    return True
