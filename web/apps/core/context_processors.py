from django.conf import settings
from apps.settings_app.models import BusinessProfile, Branch


def drivesphere_globals(request):
    business = BusinessProfile.get_solo()
    branches = Branch.objects.filter(is_active=True).order_by("name")

    active_branch_id = request.session.get(settings.ACTIVE_BRANCH_SESSION_KEY)
    active_branch = None
    if active_branch_id:
        active_branch = branches.filter(id=active_branch_id).first()

    return {
        "ds_business": business,
        "ds_branches": branches,
        "ds_active_branch": active_branch,
    }