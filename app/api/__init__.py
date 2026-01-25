# app/api/__init__.py
"""
API模块包
"""

from .routes import api_bp
from .charts import charts_bp

__all__ = ['api_bp', 'charts_bp']