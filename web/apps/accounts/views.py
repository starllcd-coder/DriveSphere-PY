from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.core.services import log_audit_event
from .forms import LoginForm


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    initial = {}
    if request.method == "GET":
        saved_lang = request.COOKIES.get("ds_login_lang")
        saved_identifier = request.COOKIES.get("ds_login_identifier")
        saved_branch = request.COOKIES.get("ds_login_branch")
        if saved_lang in ["en", "ar"]:
            request.session["ui_lang"] = saved_lang
        if saved_identifier:
            initial["identifier"] = saved_identifier
        if saved_branch:
            initial["branch"] = saved_branch

    form = LoginForm(request.POST or None, initial=initial)

    def _client_ip() -> str:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")

    def _login_limit_key(identifier: str) -> str:
        return f"web:login:limit:{_client_ip()}:{identifier.lower()}"

    def _login_block_key(identifier: str) -> str:
        return f"web:login:block:{_client_ip()}:{identifier.lower()}"

    identifier = ""
    if request.method == "POST":
        identifier = str(request.POST.get("identifier") or "").strip()
        if identifier and cache.get(_login_block_key(identifier)):
            form.add_error(None, "Too many failed attempts. Please try again later.")
            return render(request, "accounts/login.html", {"form": form})

    if request.method == "POST" and form.is_valid():
        user = form.cleaned_data["user"]
        ui_lang = request.session.get("ui_lang", "en")
        login(request, user)

        # remember_me: if unchecked, session ends on browser close
        if not form.cleaned_data.get("remember_me"):
            request.session.set_expiry(0)

        branch_id = form.resolve_branch_id()
        request.session[settings.ACTIVE_BRANCH_SESSION_KEY] = branch_id
        request.session["ui_lang"] = ui_lang
        request.session.modified = True

        # Persist language + branch to user profile
        update_fields = []
        if ui_lang in ["en", "ar"] and user.preferred_language != ui_lang:
            user.preferred_language = ui_lang
            update_fields.append("preferred_language")
        if branch_id and user.default_branch_id != branch_id:
            user.default_branch_id = branch_id
            update_fields.append("default_branch")
        if update_fields:
            user.save(update_fields=update_fields)

        response = redirect(settings.LOGIN_REDIRECT_URL)

        # Remember-me: store username/branch/lang for next login
        if form.cleaned_data.get("remember_me"):
            max_age = 60 * 60 * 24 * 30
            response.set_cookie("ds_login_identifier", form.cleaned_data.get("identifier", ""), max_age=max_age)
            response.set_cookie("ds_login_branch", branch_id or "", max_age=max_age)
            response.set_cookie("ds_login_lang", ui_lang, max_age=max_age)
        else:
            response.delete_cookie("ds_login_identifier")
            response.delete_cookie("ds_login_branch")
            response.delete_cookie("ds_login_lang")

        log_audit_event(
            action="USER_LOGIN",
            entity_type="User",
            entity_id=user.id,
            message=f"{user.email} logged in",
            request=request,
            user=user,
            metadata={"branch_id": branch_id or "", "remember_me": bool(form.cleaned_data.get("remember_me"))},
        )
        cache.delete(_login_limit_key(form.cleaned_data.get("identifier", "")))
        cache.delete(_login_block_key(form.cleaned_data.get("identifier", "")))
        return response

    if request.method == "POST" and not form.is_valid() and identifier:
        limit_key = _login_limit_key(identifier)
        block_key = _login_block_key(identifier)
        current = int(cache.get(limit_key) or 0) + 1
        cache.set(limit_key, current, timeout=settings.LOGIN_ATTEMPT_WINDOW_SECONDS)
        if current >= settings.LOGIN_ATTEMPT_LIMIT:
            cache.set(block_key, 1, timeout=settings.LOGIN_BLOCK_SECONDS)
            form.add_error(None, "Too many failed attempts. Please try again later.")

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    if getattr(request.user, "is_authenticated", False):
        log_audit_event(
            action="USER_LOGOUT",
            entity_type="User",
            entity_id=request.user.id,
            message=f"{request.user.email} logged out",
            request=request,
            user=request.user,
        )
    logout(request)
    messages.info(request, "Logged Out.")
    return redirect(settings.LOGOUT_REDIRECT_URL)
