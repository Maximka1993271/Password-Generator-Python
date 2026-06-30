"""
Tests for Secure Pass Pro v4.0
Тесты для Secure Pass Pro v4.0
Тести для Secure Pass Pro v4.0

This package contains unit tests for all modules.
Этот пакет содержит модульные тесты для всех модулей.
Цей пакет містить модульні тести для всіх модулів.

FIXED: Added proper __init__.py for test package
"""
from __future__ import annotations

import os
import sys

# Add project root to path for imports
# Добавляем корень проекта в путь для импортов
# Додаємо корінь проекту до шляху для імпортів
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# ==================== EXPORTS ====================

__all__ = [
    'conftest',
]

# ==================== TEST PACKAGE INFO ====================

__version__ = "4.0.1"
__author__ = "Maxim Melnikov"
__description__ = "Unit tests for Secure Pass Pro v4.0" 
