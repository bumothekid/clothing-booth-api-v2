from app.utils.exceptions.base import OutfitValidationError

class OutfitIDMissingError(OutfitValidationError):
    def __init__(self, message="Outfit ID is missing"):
        super().__init__(message)

class OutfitClothingIDsMissingError(OutfitValidationError):
    def __init__(self, message="Outfit clothing ID(s) are missing"):
        super().__init__(message)

class OutfitNameMissingError(OutfitValidationError):
    def __init__(self, message="Outfit name is missing"):
        super().__init__(message)
        
class OutfitClothingIDInvalidError(OutfitValidationError):
    def __init__(self, message="Outfit clothing ID is invalid"):
        super().__init__(message)
        
class OutfitSeasonsInvalidError(OutfitValidationError):
    def __init__(self, message="Outfit seasons are invalid"):
        super().__init__(message)

class OutfitTagsInvalidError(OutfitValidationError):
    def __init__(self, message="Outfit tags are invalid"):
        super().__init__(message)
        
class OutfitLimitInvalidError(OutfitValidationError):
    def __init__(self, message="Outfit limit is invalid."):
        super().__init__(message)
        
class OutfitOffsetInvalidError(OutfitValidationError):
    def __init__(self, message="Outfit offset is invalid."):
        super().__init__(message)
        
class OutfitNameTooShortError(OutfitValidationError):
    def __init__(self, message="Outfit name is too short."):
        super().__init__(message)

class OutfitNameTooLongError(OutfitValidationError):
    def __init__(self, message="Outfit name is too long."):
        super().__init__(message)

class OutfitDescriptionTooLongError(OutfitValidationError):
    def __init__(self, message="Outfit description is too long."):
        super().__init__(message)