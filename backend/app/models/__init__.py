"""
SQL Models - Only User is stored in PostgreSQL.
All other data (products, categories, cart, orders) is stored in MongoDB.
"""

from app.models.base import Base
from app.models.user import User

__all__ = ["Base", "User"]
