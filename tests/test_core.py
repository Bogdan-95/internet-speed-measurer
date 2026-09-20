"""Тесты для модуля core.py."""

import unittest
from unittest.mock import MagicMock, patch

from speed_measurer.core import (
    CHUNK_SIZE,
    RequestResult,
    measure_single_request,
    run_speed_test,
)
from speed_measurer.exceptions import InvalidURLError


def make_mock_response(data: bytes) -> MagicMock:
    """Создаёт MagicMock, имитирующий потоковое чтение ответа.

    Возвращает мок, который отдаёт `data` чанками по CHUNK_SIZE байт,
    а затем — пустой байт (признак конца).

    Args:
        data: Данные, которые должен «отдать» мок.

    Returns:
        Настроенный MagicMock.
    """
    mock_response = MagicMock()
    chunks = [data[i : i + CHUNK_SIZE] for i in range(0, len(data), CHUNK_SIZE)]
    chunks.append(b"")  # конец потока
    mock_response.read.side_effect = chunks
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


class TestValidateURL(unittest.TestCase):
    """Тесты валидации URL."""

    @patch("speed_measurer.core.request")
    def test_valid_url_success(self, mock_request: MagicMock) -> None:
        """Успешный запрос с валидным URL."""
        mock_request.urlopen.return_value = make_mock_response(b"x" * 1_000_000)

        result = measure_single_request("https://example.com/file.bin")

        self.assertTrue(result.success)
        self.assertEqual(result.bytes_downloaded, 1_000_000)
        self.assertGreater(result.elapsed_time, 0)

    def test_empty_url_raises_error(self) -> None:
        """Пустой URL вызывает InvalidURLError."""
        with self.assertRaises(InvalidURLError):
            measure_single_request("")

    def test_whitespace_url_raises_error(self) -> None:
        """URL с пробелами вызывает InvalidURLError."""
        with self.assertRaises(InvalidURLError):
            measure_single_request("   ")

    def test_url_without_scheme_raises_error(self) -> None:
        """URL без схемы http/https вызывает InvalidURLError."""
        with self.assertRaises(InvalidURLError) as context:
            measure_single_request("example.com/file.bin")
        self.assertIn("http://", str(context.exception))

    def test_ftp_scheme_raises_error(self) -> None:
        """URL с FTP-схемой вызывает InvalidURLError."""
        with self.assertRaises(InvalidURLError):
            measure_single_request("ftp://example.com/file.bin")


class TestMeasureSingleRequest(unittest.TestCase):
    """Тесты функции measure_single_request."""

    @patch("speed_measurer.core.request")
    def test_returns_request_result(self, mock_request: MagicMock) -> None:
        """Функция возвращает RequestResult."""
        mock_request.urlopen.return_value = make_mock_response(b"data")

        result = measure_single_request("https://example.com/test.bin")

        self.assertIsInstance(result, RequestResult)
        self.assertTrue(result.success)
        self.assertEqual(result.bytes_downloaded, 4)

    @patch("speed_measurer.core.request")
    def test_chunked_reading(self, mock_request: MagicMock) -> None:
        """Ответ читается чанками (не одним вызовом read)."""
        big_data = b"x" * (CHUNK_SIZE * 3 + 100)  # 3 полных чанка + хвост
        mock_response = make_mock_response(big_data)
        mock_request.urlopen.return_value = mock_response

        result = measure_single_request("https://example.com/big.bin")

        self.assertTrue(result.success)
        self.assertEqual(result.bytes_downloaded, len(big_data))
        # 3 полных чанка + 1 хвост + 1 пустой = минимум 5 вызовов
        self.assertGreaterEqual(mock_response.read.call_count, 5)

    @patch("speed_measurer.core.request")
    def test_timeout_error_handling(self, mock_request: MagicMock) -> None:
        """Таймаут корректно обрабатывается."""
        mock_request.urlopen.side_effect = TimeoutError("timed out")

        result = measure_single_request("https://example.com/test.bin")

        self.assertFalse(result.success)
        self.assertEqual(result.bytes_downloaded, 0)
        self.assertIn("Таймаут", result.error_message)


class TestRunSpeedTest(unittest.TestCase):
    """Тесты функции run_speed_test."""

    @patch("speed_measurer.core.measure_single_request")
    def test_runs_correct_count(self, mock_measure: MagicMock) -> None:
        """Выполняется ровно указанное количество запросов."""
        mock_measure.return_value = RequestResult(
            success=True, bytes_downloaded=1000, elapsed_time=0.5
        )

        results = run_speed_test("https://example.com/file.bin", count=5)

        self.assertEqual(len(results), 5)
        self.assertEqual(mock_measure.call_count, 5)

    @patch("speed_measurer.core.measure_single_request")
    def test_collects_results(self, mock_measure: MagicMock) -> None:
        """Результаты собираются корректно."""
        mock_measure.side_effect = [
            RequestResult(success=True, bytes_downloaded=1000, elapsed_time=0.5),
            RequestResult(
                success=False,
                bytes_downloaded=0,
                elapsed_time=0.0,
                error_message="Error",
            ),
        ]

        results = run_speed_test("https://example.com/file.bin", count=2)

        self.assertTrue(results[0].success)
        self.assertFalse(results[1].success)

    @patch("speed_measurer.core.measure_single_request")
    def test_progress_callback_called(self, mock_measure: MagicMock) -> None:
        """progress_callback вызывается для каждого запроса."""
        mock_measure.return_value = RequestResult(
            success=True, bytes_downloaded=100, elapsed_time=0.1
        )
        calls: list[tuple[int, int]] = []

        def cb(current: int, total: int, result: RequestResult) -> None:
            calls.append((current, total))

        run_speed_test("https://example.com/f.bin", count=3, progress_callback=cb)

        self.assertEqual(calls, [(1, 3), (2, 3), (3, 3)])

    @patch("speed_measurer.core.measure_single_request")
    def test_progress_callback_none_by_default(self, mock_measure: MagicMock) -> None:
        """Без callback функция не падает."""
        mock_measure.return_value = RequestResult(
            success=True, bytes_downloaded=100, elapsed_time=0.1
        )

        # Не должно быть исключений
        run_speed_test("https://example.com/f.bin", count=2)


if __name__ == "__main__":
    unittest.main()
