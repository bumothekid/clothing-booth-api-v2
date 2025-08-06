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
    
class OutfitNameTooShortError(OutfitValidationError):
    def __init__(self, message="Outfit name has to be at least 3 characters long"):
        super().__init__(message)

class OutfitNameTooLongError(OutfitValidationError):
    def __init__(self, message="Outfit name has to be at most 50 characters long"):
        super().__init__(message)

class OutfitDescriptionTooLongError(OutfitValidationError):
    def __init__(self, message="Outfit description has to be at most 255 characters long"):
        super().__init__(message)