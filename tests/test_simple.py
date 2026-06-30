"""
Simple test to verify pytest works.
"""
from __future__ import annotations
import pytest


def test_simple():
    """Simple test that always passes."""
    assert True


def test_addition():
    """Test basic addition."""
    assert 1 + 1 == 2


def test_string():
    """Test string operations."""
    assert "hello".upper() == "HELLO"


def test_list():
    """Test list operations."""
    assert len([1, 2, 3]) == 3


def test_dict():
    """Test dict operations."""
    d = {"a": 1, "b": 2}
    assert d["a"] == 1
    assert "c" not in d