from fastapi import HTTPException, status

class EmergencyAppException(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class InvalidInputException(EmergencyAppException):
    def __init__(self, message: str = "Invalid emergency input provided"):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST)

class UnsupportedMediaException(EmergencyAppException):
    def __init__(self, message: str = "Unsupported media file format or file size"):
        super().__init__(message=message, status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

class LowConfidenceEscalationException(EmergencyAppException):
    def __init__(self, message: str = "Medical guidance withheld due to low retrieval relevance or unverified evidence"):
        super().__init__(message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

class LLMProviderException(EmergencyAppException):
    def __init__(self, message: str = "LLM provider connection or generation error"):
        super().__init__(message=message, status_code=status.HTTP_502_BAD_GATEWAY)
