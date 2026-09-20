"""Тесты для модуля report.py."""

import unittest

from speed_measurer.core import RequestResult
from speed_measurer.report import calculate_statistics, format_report


class TestCalculateStatistics(unittest.TestCase):
    """Тесты функции calculate_statistics."""

    def test_all_successful(self) -> None:
        """Все запросы успешны."""
        results = [
            RequestResult(success=True, bytes_downloaded=1_000_000, elapsed_time=1.0),
            RequestResult(success=True, bytes_downloaded=2_000_000, elapsed_time=2.0),
            RequestResult(success=True, bytes_downloaded=3_000_000, elapsed_time=3.0),
        ]

        stats = calculate_statistics(results)

        self.assertEqual(stats["total_requests"], 3)
        self.assertEqual(stats["successful"], 3)
        self.assertEqual(stats["failed"], 0)
        self.assertEqual(stats["total_bytes"], 6_000_000)
        self.assertEqual(stats["total_time"], 6.0)
        self.assertAlmostEqual(stats["avg_time"], 2.0)
        # 6 MB / 6 sec = 1.0 MB/sec
        self.assertAlmostEqual(stats["avg_speed_mbps"], 1.0)

    def test_mixed_results(self) -> None:
        """Смешанные результаты (успешные и неуспешные)."""
        results = [
            RequestResult(success=True, bytes_downloaded=1_000_000, elapsed_time=1.0),
            RequestResult(success=False, bytes_downloaded=0, elapsed_time=0.0),
            RequestResult(success=True, bytes_downloaded=2_000_000, elapsed_time=2.0),
        ]

        stats = calculate_statistics(results)

        self.assertEqual(stats["successful"], 2)
        self.assertEqual(stats["failed"], 1)
        self.assertEqual(stats["total_bytes"], 3_000_000)
        self.assertEqual(stats["total_time"], 3.0)
        # 3 MB / 3 sec = 1.0 MB/sec
        self.assertAlmostEqual(stats["avg_speed_mbps"], 1.0)

    def test_all_failed(self) -> None:
        """Все запросы неуспешны."""
        results = [
            RequestResult(success=False, bytes_downloaded=0, elapsed_time=0.0),
            RequestResult(success=False, bytes_downloaded=0, elapsed_time=0.0),
        ]

        stats = calculate_statistics(results)

        self.assertEqual(stats["successful"], 0)
        self.assertEqual(stats["failed"], 2)
        self.assertEqual(stats["total_bytes"], 0)
        self.assertEqual(stats["total_time"], 0.0)
        self.assertEqual(stats["avg_speed_mbps"], 0.0)

    def test_speed_calculation_formula(self) -> None:
        """Проверка формулы скорости: MB / сек."""
        # 5 MB за 10 секунд = 0.5 MB/sec
        results = [
            RequestResult(success=True, bytes_downloaded=5_000_000, elapsed_time=10.0),
        ]

        stats = calculate_statistics(results)

        self.assertAlmostEqual(stats["avg_speed_mbps"], 0.5)


class TestFormatReport(unittest.TestCase):
    """Тесты функции format_report."""

    def test_report_contains_key_metrics(self) -> None:
        """Отчёт содержит ключевые метрики."""
        results = [
            RequestResult(success=True, bytes_downloaded=2_000_000, elapsed_time=2.0),
            RequestResult(success=True, bytes_downloaded=3_000_000, elapsed_time=3.0),
        ]

        report = format_report(results)

        self.assertIn("РЕЗУЛЬТАТЫ ЗАМЕРА СКОРОСТИ", report)
        self.assertIn("Всего запросов:", report)
        self.assertIn("Успешных:", report)
        self.assertIn("Неуспешных:", report)
        self.assertIn("СКОРОСТЬ", report)

    def test_report_shows_speed_value(self) -> None:
        """Отчёт показывает значение скорости."""
        results = [
            RequestResult(success=True, bytes_downloaded=5_000_000, elapsed_time=5.0),
        ]

        report = format_report(results)

        # 5 MB / 5 sec = 1.0 MB/sec
        self.assertIn("1.000 МБ/сек", report)


if __name__ == "__main__":
    unittest.main()
