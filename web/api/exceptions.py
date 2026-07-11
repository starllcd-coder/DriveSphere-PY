from rest_framework.views import exception_handler


def standard_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    payload = {
        "ok": False,
        "error": "Request failed.",
        "details": response.data,
    }

    if isinstance(response.data, dict):
        if "detail" in response.data and isinstance(response.data["detail"], str):
            payload["error"] = response.data["detail"]
        elif "error" in response.data and isinstance(response.data["error"], str):
            payload["error"] = response.data["error"]
    response.data = payload
    return response
