__all__ = ["helper"]

from typing import Any
from app.utils.logging import get_logger

logger = get_logger()

class HelperFunctions:
    @staticmethod
    def ensure_dict(result: Any) -> dict:
        """
        :param result: The object to check
        :return: Result as dictionary
        :raises TypeError: If result is not a dictionary
        """
        if not isinstance(result, dict):
            raise TypeError(f"Expected a dictionary, but got {type(result).__name__}")
        
        return result
    
    @staticmethod
    def build_paginated_response(items, limit, offset, total):
        return {
            "items": items,
            "limit": limit,
            "offset": offset,
            "total": total
        }

helper = HelperFunctions()