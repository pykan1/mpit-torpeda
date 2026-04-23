class DriveeryException(Exception):
    """Base domain exception."""
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class GuardrailViolation(DriveeryException):
    def __init__(self, message: str):
        super().__init__(message, "GUARDRAIL_VIOLATION")


class SQLExecutionError(DriveeryException):
    def __init__(self, message: str):
        super().__init__(message, "SQL_EXECUTION_ERROR")


class AIServiceError(DriveeryException):
    def __init__(self, message: str):
        super().__init__(message, "AI_SERVICE_ERROR")


class NotFoundError(DriveeryException):
    def __init__(self, resource: str):
        super().__init__(f"{resource} not found", "NOT_FOUND")
