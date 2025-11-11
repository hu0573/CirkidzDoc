"""
Cirkidz 文档模板后端应用包。

此模块暴露 create_app 工厂函数以便于可测试性与可配置化。
"""

from .main import create_app, app

__all__ = ["create_app", "app"]

