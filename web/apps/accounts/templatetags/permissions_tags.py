from django import template

from apps.accounts.permissions import has_perm as has_perm_func

register = template.Library()


@register.filter(name="has_perm")
def has_perm_filter(user, perm_code):
    try:
        return bool(has_perm_func(user, perm_code))
    except Exception:
        return False
