from typing import Any, Dict, Optional


def ok(message: str = "", data: Optional[Any] = None) -> Dict[str, Any]:
    return {"success": True, "message": message, "data": data}


def error(message: str, code: Optional[str] = None, data: Optional[Any] = None) -> Dict[str, Any]:
    body: Dict[str, Any] = {"success": False, "message": message}
    if code is not None:
        body["code"] = code
    if data is not None:
        body["data"] = data
    return body


def from_exception(exc: Exception, code: Optional[str] = None) -> Dict[str, Any]:
    return error(str(exc), code=code)


