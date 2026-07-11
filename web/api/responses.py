from rest_framework import status
from rest_framework.response import Response

from .pagination import StandardResultsSetPagination


def api_ok(data=None, message: str = "", http_status: int = status.HTTP_200_OK, **extra):
    body = {"ok": True}
    if message:
        body["message"] = message
    if data is not None:
        body["data"] = data
    if extra:
        body.update(extra)
    return Response(body, status=http_status)


def api_error(error: str, *, details=None, http_status: int = status.HTTP_400_BAD_REQUEST, **extra):
    body = {"ok": False, "error": error}
    if details is not None:
        body["details"] = details
    if extra:
        body.update(extra)
    return Response(body, status=http_status)


def paginated_list_response(request, queryset, serializer_class):
    paginator = StandardResultsSetPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = serializer_class(page, many=True, context={"request": request})
    return paginator.get_paginated_response(serializer.data)
