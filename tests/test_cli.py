"""Тесты для модуля cli.py."""

import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest.mock import MagicMock, patch

from speed_measurer.cli import main, parse_args
from speed_measurer.core import RequestResult


class TestParseArgs(unittest.TestCase):
    """Тесты функции parse_args."""

    def test_no_args_returns_none_url(self) -> None:
        """Без аргументов URL = None."""
        args = parse_args([])
        self.assertIsNone(args.url)

    def test_url_argument(self) -> None:
        """URL передаётся как позиционный аргумент."""
        args = parse_args(["https://example.com/file.bin"])
        self.assertEqual(args.url, "https://example.com/file.bin")

    def test_count_option(self) -> None:
        """Количество запросов через -c/--count."""
        args = parse_args(["-c", "5", "https://example.com/file.bin"])
        self.assertEqual(args.count, 5)

        args2 = parse_args(["--count", "3", "https://example.com/file.bin"])
        self.assertEqual(args2.count, 3)

    def test_default_count(self) -> None:
        """По умолчанию 10 запросов."""
        args = parse_args(["https://example.com/file.bin"])
        self.assertEqual(args.count, 10)


class TestMain(unittest.TestCase):
    """Тесты функции main.

    В setUp/tearDown глушим stdout/stderr, чтобы main() не засорял
    консоль реальным выводом во время тестов.
    """

    def setUp(self) -> None:
        self._stdout_buf = StringIO()
        self._stderr_buf = StringIO()
        self._stdout_ctx = redirect_stdout(self._stdout_buf)
        self._stderr_ctx = redirect_stderr(self._stderr_buf)
        self._stdout_ctx.__enter__()
        self._stderr_ctx.__enter__()

    def tearDown(self) -> None:
        self._stdout_ctx.__exit__(None, None, None)
        self._stderr_ctx.__exit__(None, None, None)

    @patch("speed_measurer.cli.run_speed_test")
    @patch("speed_measurer.cli.print_report")
    def test_success_exit_code(
        self, mock_print: MagicMock, mock_run: MagicMock
    ) -> None:
        """Успешный замер возвращает код 0."""
        mock_run.return_value = [
            RequestResult(success=True, bytes_downloaded=1_000_000, elapsed_time=1.0)
        ]
        mock_print.return_value = True

        exit_code = main(["https://example.com/file.bin"])

        self.assertEqual(exit_code, 0)

    @patch("speed_measurer.cli.run_speed_test")
    @patch("speed_measurer.cli.print_report")
    def test_all_failed_exit_code(
        self, mock_print: MagicMock, mock_run: MagicMock
    ) -> None:
        """Все запросы неуспешны — код 1."""
        mock_run.return_value = [
            RequestResult(success=False, bytes_downloaded=0, elapsed_time=0.0)
        ]
        mock_print.return_value = False

        exit_code = main(["https://example.com/file.bin"])

        self.assertEqual(exit_code, 1)

    def test_invalid_url_exit_code(self) -> None:
        """Некорректный URL — код 1, в stderr есть сообщение об ошибке."""
        exit_code = main(["not-a-valid-url"])

        self.assertEqual(exit_code, 1)
        self.assertIn("Ошибка", self._stderr_buf.getvalue())

    def test_empty_url_exit_code(self) -> None:
        """Пустой URL — код 1."""
        exit_code = main([""])

        self.assertEqual(exit_code, 1)

    def test_invalid_count_exit_code(self) -> None:
        """--count 0 — код 1, сообщение об ошибке."""
        exit_code = main(["-c", "0", "https://example.com/file.bin"])

        self.assertEqual(exit_code, 1)
        self.assertIn("количество запросов", self._stderr_buf.getvalue())

    def test_negative_count_exit_code(self) -> None:
        """--count -5 — код 1."""
        exit_code = main(["-c", "-5", "https://example.com/file.bin"])

        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
