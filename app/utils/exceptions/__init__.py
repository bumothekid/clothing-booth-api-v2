from app.utils.exceptions.base import (
    ValidationError,
    NotFoundError,
    ConflictError,
    ClothingValidationError,
    ClothingNotFoundError,
    ClothingConflictError,
    OutfitValidationError,
    OutfitNotFoundError,
    AuthValidationError
)

from app.utils.exceptions.validation import UnsupportedFileTypeError, FileTooLargeError, ImageUnclearError
from app.utils.exceptions.clothing import (
    ClothingIDMissingError,
    ClothingNameMissingError,
    ClothingCategoryMissingError,
    ClothingColorMissingError,
    ClothingImageMissingError,
    ClothingNameTooShortError,
    ClothingNameTooLongError,
    ClothingDescriptionTooLongError,
    ClothingImageInvalidError
)
from app.utils.exceptions.outfits import (
    OutfitIDMissingError,
    OutfitNameMissingError,
    OutfitNameTooShortError,
    OutfitNameTooLongError,
    OutfitDescriptionTooLongError
)
from app.utils.exceptions.auth import AuthTokenExpiredError, AuthAccessTokenInvalidError, AuthRefreshTokenInvalidError, AuthAccessTokenMissingError, AuthRefreshTokenMissingError, AuthUserIDMissingError

__all__ = [
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "ClothingValidationError",
    "ClothingNotFoundError",
    "ClothingConflictError",
    "AuthValidationError",
    "UnsupportedFileTypeError",
    "FileTooLargeError",
    "ImageUnclearError",
    "ClothingNameMissingError",
    "ClothingCategoryMissingError",
    "ClothingColorMissingError",
    "ClothingIDMissingError",
    "ClothingImageMissingError",
    "ClothingNameTooShortError",
    "ClothingNameTooLongError",
    "ClothingDescriptionTooLongError",
    "ClothingImageInvalidError",
    "OutfitValidationError",
    "OutfitNotFoundError",
    "OutfitIDMissingError",
    "OutfitNameMissingError",
    "OutfitNameTooShortError",
    "OutfitNameTooLongError",
    "OutfitDescriptionTooLongError",
    "AuthTokenExpiredError",
    "AuthAccessTokenInvalidError",
    "AuthRefreshTokenInvalidError",
    "AuthAccessTokenMissingError",
    "AuthRefreshTokenMissingError",
    "AuthUserIDMissingError"
]