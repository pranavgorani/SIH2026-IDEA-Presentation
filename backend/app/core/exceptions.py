from typing import Optional, Dict, Any

class BaseScreeningException(Exception):
    def __init__(
        self,
        message: str,
        code: str = "SCREENING_ERROR",
        stage: str = "GATEWAY",
        http_status: int = 500,
        recoverable: bool = True,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.stage = stage
        self.http_status = http_status
        self.recoverable = recoverable
        self.details = details or {}

class InvalidDocumentException(BaseScreeningException):
    def __init__(self, message: str = "Invalid or corrupted document format.", code: str = "INVALID_DOCUMENT", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code=code, stage="FILE_VALIDATION", http_status=400, recoverable=True, details=details)

class FileTooLargeException(BaseScreeningException):
    def __init__(self, message: str = "Uploaded file exceeds maximum allowed limit of 25MB.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="FILE_TOO_LARGE", stage="FILE_VALIDATION", http_status=413, recoverable=True, details=details)

class DocumentNotFoundException(BaseScreeningException):
    def __init__(self, message: str = "Document or case not found.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="DOCUMENT_NOT_FOUND", stage="GATEWAY", http_status=404, recoverable=False, details=details)

class UnauthorizedException(BaseScreeningException):
    def __init__(self, message: str = "Authentication credentials required or invalid.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="UNAUTHORIZED", stage="GATEWAY", http_status=401, recoverable=False, details=details)

class ForbiddenException(BaseScreeningException):
    def __init__(self, message: str = "Insufficient permissions for requested operation.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="FORBIDDEN", stage="GATEWAY", http_status=403, recoverable=False, details=details)

class AIServiceUnavailableException(BaseScreeningException):
    def __init__(self, message: str = "Upstream AI vision model unavailable. Falling back to local verification.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="AI_SERVICE_UNAVAILABLE", stage="VISUAL_FORENSICS", http_status=502, recoverable=True, details=details)
