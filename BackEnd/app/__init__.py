"""
Cirkidz document template backend package.

This module exposes the create_app factory for testability and configurability.
"""

from .main import create_app, app

__all__ = ["create_app", "app"]

