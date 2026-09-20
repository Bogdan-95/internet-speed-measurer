"""Кастомные исключения для speed_measurer."""


class SpeedMeasurerError(Exception):
    """Базовое исключение для ошибок замера скорости."""


class InvalidURLError(SpeedMeasurerError):
    """Исключение для некорректного URL."""
