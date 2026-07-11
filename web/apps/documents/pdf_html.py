from __future__ import annotations

import os
import re

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string


def _inject_base_tag(html: str, base_url: str) -> str:
    if not base_url:
        return html
    if re.search(r"<base\s+href=", html, flags=re.IGNORECASE):
        return html
    return re.sub(
        r"<head(\s[^>]*)?>",
        lambda m: f"{m.group(0)}\n  <base href=\"{base_url}\">",
        html,
        count=1,
        flags=re.IGNORECASE,
    )


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-_")
    return cleaned or "document"


def _save_pdf_copy(pdf_bytes: bytes, subdir: str | None, filename: str) -> str | None:
    if not subdir:
        return None
    base_dir = getattr(settings, "MEDIA_ROOT", "")
    if not base_dir:
        return None
    folder = os.path.join(base_dir, "exports", subdir)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    with open(path, "wb") as f:
        f.write(pdf_bytes)
    return path


def render_pdf_from_template(
    *,
    request,
    template: str,
    context: dict,
    filename: str,
    export_subdir: str | None = None,
) -> HttpResponse:
    # Import lazily so backend startup/migrations do not fail on environments
    # where Playwright runtime is intentionally not bundled.
    from playwright.sync_api import sync_playwright

    html = render_to_string(template, context, request=request)
    base_url = request.build_absolute_uri("/")
    html = _inject_base_tag(html, base_url)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        page.emulate_media(media="print")
        pdf_bytes = page.pdf(format="A4", print_background=True)
        browser.close()

    safe_name = _safe_filename(filename)
    _save_pdf_copy(pdf_bytes, export_subdir, safe_name)
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{safe_name}"'
    return resp
