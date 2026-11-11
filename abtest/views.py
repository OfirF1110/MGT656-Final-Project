import random
from fractions import Fraction

from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import Visit

# Course nicknames of the four team members (see docs/mgt656/team.yaml).
TEAM_NICKNAMES = [
    "brainy-squid",
    "amused-cobra",
    "outstanding-flamingo",
    "cooperative-butterfly",
]
VARIANTS = (Visit.KUDOS, Visit.THANKS)
SESSION_KEY = "abtest_visitor_id"


def _existing_visit(request):
    """Return this visitor's Visit, or None. Never creates anything."""
    visitor_id = request.session.get(SESSION_KEY)
    if not visitor_id:
        return None
    return Visit.objects.filter(visitor_id=visitor_id).first()


def _visit_for_page_view(request):
    """Return this visitor's Visit, creating it (one impression) on first sight."""
    visit = _existing_visit(request)
    if visit is None:
        visit = Visit.objects.create(variant=random.choice(VARIANTS))
        request.session[SESSION_KEY] = str(visit.visitor_id)
    return visit


@require_http_methods(["GET", "POST"])
def ab_page(request):
    if request.method == "POST":
        visit = _existing_visit(request)
        if visit is not None:
            # Only the first click is stored; later clicks match no row.
            Visit.objects.filter(pk=visit.pk, clicked_at__isnull=True).update(
                clicked_at=timezone.now()
            )
        return redirect(request.path)
    visit = _visit_for_page_view(request)
    return render(
        request,
        "abtest/page.html",
        {"variant": visit.variant, "nicknames": TEAM_NICKNAMES},
    )


def _click_rate(counts):
    if counts["impressions"] == 0:
        return Fraction(0)
    return Fraction(counts["clicks"], counts["impressions"])


def ab_stats(request):
    counts = {v: {"impressions": 0, "clicks": 0} for v in VARIANTS}
    rows = Visit.objects.values("variant").annotate(
        impressions=Count("id"), clicks=Count("clicked_at")
    )
    for row in rows:
        counts[row["variant"]] = {
            "impressions": row["impressions"],
            "clicks": row["clicks"],
        }
    # Fixed tie rule: kudos wins unless thanks is strictly better.
    if _click_rate(counts[Visit.THANKS]) > _click_rate(counts[Visit.KUDOS]):
        preferred = Visit.THANKS
    else:
        preferred = Visit.KUDOS
    return JsonResponse({"preferred": preferred, **counts})
