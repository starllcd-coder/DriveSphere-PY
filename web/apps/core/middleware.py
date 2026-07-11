from django.conf import settings


class ActiveBranchMiddleware:
    """
    Ensures the session key exists.
    Actual value is set in login flow.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.ACTIVE_BRANCH_SESSION_KEY not in request.session:
            request.session[settings.ACTIVE_BRANCH_SESSION_KEY] = None
        if "ui_lang" not in request.session:
            if hasattr(request, "user") and getattr(request.user, "is_authenticated", False):
                request.session["ui_lang"] = getattr(request.user, "preferred_language", "en") or "en"
            else:
                request.session["ui_lang"] = "en"
        return self.get_response(request)