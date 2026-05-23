from fastapi import HTTPException, status


class ApiError(HTTPException):
    def __init__(self, code: str, message: str, status_code: int = 400, **extra):
        detail = {"code": code, "message": message, **extra}
        super().__init__(status_code=status_code, detail=detail)


def unauthorized(message: str = "Не авторизован", code: str = "unauthorized") -> ApiError:
    return ApiError(code, message, status_code=status.HTTP_401_UNAUTHORIZED)


def forbidden(message: str = "Доступ запрещён", code: str = "forbidden") -> ApiError:
    return ApiError(code, message, status_code=status.HTTP_403_FORBIDDEN)


def not_found(message: str = "Не найдено", code: str = "not_found") -> ApiError:
    return ApiError(code, message, status_code=status.HTTP_404_NOT_FOUND)


def bad_request(message: str, code: str = "bad_request", **extra) -> ApiError:
    return ApiError(code, message, status_code=status.HTTP_400_BAD_REQUEST, **extra)


def conflict(message: str, code: str = "conflict", **extra) -> ApiError:
    return ApiError(code, message, status_code=status.HTTP_409_CONFLICT, **extra)
