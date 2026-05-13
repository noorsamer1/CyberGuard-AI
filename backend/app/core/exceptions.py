from fastapi import HTTPException, status


class AppHTTPException(HTTPException):
    def __init__(self, status_code: int, detail: str, code: str = "error") -> None:
        super().__init__(status_code=status_code, detail={"message": detail, "code": code})


def not_found(msg: str = "Resource not found") -> AppHTTPException:
    return AppHTTPException(status.HTTP_404_NOT_FOUND, msg, "not_found")


def bad_request(msg: str) -> AppHTTPException:
    return AppHTTPException(status.HTTP_400_BAD_REQUEST, msg, "bad_request")


def unauthorized(msg: str = "Not authenticated") -> AppHTTPException:
    return AppHTTPException(status.HTTP_401_UNAUTHORIZED, msg, "unauthorized")


def forbidden(msg: str = "Forbidden") -> AppHTTPException:
    return AppHTTPException(status.HTTP_403_FORBIDDEN, msg, "forbidden")
