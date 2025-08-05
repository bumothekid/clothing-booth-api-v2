class ValidationError(Exception):
    def __init__(self, message="Validation error occurred"):
        super().__init__(message)
        
class NotFoundError(Exception):
    def __init__(self, message="Resource not found"):
        super().__init__(message)

class ConflictError(Exception):
    def __init__(self, message="Conflict occurred"):
        super().__init__(message)

# Clothing

class ClothingValidationError(ValidationError):
    def __init__(self, message="Clothing validation error occurred"):
        super().__init__(message)

class ClothingNotFoundError(NotFoundError):
    def __init__(self, message="Clothing not found"):
        super().__init__(message)

class ClothingConflictError(ConflictError):
    def __init__(self, message="Clothing conflict error occurred"):
        super().__init__(message)
        
# Authentication

class AuthValidationError(ValidationError):
    def __init__(self, message="Authentication validation error occurred"):
        super().__init__(message)