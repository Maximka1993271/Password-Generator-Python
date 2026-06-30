"""
Tests for extended logging utilities.
Тесты для расширенных утилит логирования.
Тести для розширених утиліт логування.
"""
from __future__ import annotations
import pytest
import logging
from unittest.mock import MagicMock, patch

from utils.logging_ext import (
    LogContext,
    log_error_with_context,
    log_function_call,
    log_operation
)


class TestLoggingExt:
    """Test extended logging utilities."""

    def test_log_context(self):
        """Test LogContext context manager."""
        with LogContext(test_key="test_value"):
            context = LogContext.get_context()
            assert context['test_key'] == "test_value"

        context = LogContext.get_context()
        assert 'test_key' not in context

    def test_log_context_nested(self):
        """Test nested LogContext."""
        with LogContext(outer="outer_value"):
            with LogContext(inner="inner_value"):
                context = LogContext.get_context()
                assert context['outer'] == "outer_value"
                assert context['inner'] == "inner_value"

            context = LogContext.get_context()
            assert context['outer'] == "outer_value"
            assert 'inner' not in context

    def test_log_error_with_context(self):
        """Test log_error_with_context function."""
        # Create a mock logger
        mock_logger = MagicMock()
        
        with patch('utils.logging_ext.logger', mock_logger):
            try:
                raise ValueError("Test error")
            except ValueError as e:
                with LogContext(operation="test_op", key="value"):
                    log_error_with_context(e, "Test message", {"key": "value"})

            # Verify that error was logged
            mock_logger.error.assert_called()
            call_args = str(mock_logger.error.call_args)
            assert "Test message" in call_args or "Test error" in call_args

    def test_log_function_call_decorator(self):
        """Test log_function_call decorator."""
        mock_logger = MagicMock()
        
        @log_function_call(mock_logger)
        def test_func(a, b, c=3):
            """
            Handle test func.
            Обработать test func.
            Обробити test func.
            """
            return a + b + c

        result = test_func(1, 2, c=4)
        assert result == 7

        # Verify that function call was logged
        mock_logger.debug.assert_called()
        call_args = str(mock_logger.debug.call_args)
        assert "test_func" in call_args or "RETURN" in call_args

    def test_log_function_call_decorator_class(self):
        """Test log_function_call decorator on class method."""
        mock_logger = MagicMock()
        
        class TestClass:
            @log_function_call(mock_logger)
            def test_method(self, x):
                """
                Handle test method.
                Обработать test method.
                Обробити test method.
                """
                return x * 2

        obj = TestClass()
        result = obj.test_method(5)
        assert result == 10

        # Verify that method call was logged
        mock_logger.debug.assert_called()
        call_args = str(mock_logger.debug.call_args)
        assert "test_method" in call_args or "RETURN" in call_args

    def test_log_operation_context_manager(self):
        """Test log_operation context manager."""
        mock_logger = MagicMock()
        
        with patch('utils.logging_ext.logger', mock_logger):
            # Use default log_level="info" (not debug)
            with log_operation("test_operation"):
                pass

            # Verify that operation was logged
            mock_logger.info.assert_called()
            call_args = str(mock_logger.info.call_args)
            assert "test_operation" in call_args

    def test_log_operation_with_error(self):
        """Test log_operation context manager with error."""
        mock_logger = MagicMock()
        
        with patch('utils.logging_ext.logger', mock_logger):
            try:
                with log_operation("failing_operation"):
                    raise ValueError("Operation failed")
            except ValueError:
                pass

            # Verify that error was logged
            mock_logger.error.assert_called()
            call_args = str(mock_logger.error.call_args)
            assert "failing_operation" in call_args


if __name__ == '__main__':
    pytest.main([__file__, '-v'])