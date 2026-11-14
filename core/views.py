from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render

def home(request):
    if request.user.is_authenticated:
        return redirect("contacts:list")
    return render(request, "home.html")

@login_required
def account(request):
    return render(request, "account.html")

def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})


SWATCHES = [
    ("Ink", "#131A2A", "Sidebar, top bar, toasts"),
    ("Canvas", "#F5F6F8", "Page background"),
    ("Surface", "#FFFFFF", "Panels, tables, cards"),
    ("Line", "#E2E5EA", "Borders and dividers"),
    ("Text", "#1A2130", "Body text"),
    ("Muted", "#5D6677", "Secondary text"),
    ("Accent", "#4C5BD4", "Primary buttons, links, focus, active stages"),
    ("Met green", "#1F8A5B", "Met stage icon only"),
    ("Danger", "#B3261E", "Destructive actions and errors"),
]


@login_required
def styleguide(request):
    """Living reference for the UI kit. Staff only."""
    if not request.user.is_staff:
        raise Http404
    from contacts.forms import ContactForm
    from contacts.models import STAGE_MENU, Contact, Stage

    samples = [
        Contact(pk=0, name="Amy Chen", role="VP", company="Goldman Sachs", stage=Stage.MET),
        Contact(pk=0, name="David Roy", role="Associate", company="McKinsey", stage=Stage.IN_CONVERSATION),
        Contact(pk=0, name="Tom Wu", company="Citadel", stage=Stage.INACTIVE),
    ]
    error_form = ContactForm(data={"name": "", "stage": Stage.TO_CONTACT})
    error_form.is_valid()
    return render(request, "styleguide.html", {
        "swatches": SWATCHES,
        "stages": Stage,
        "stage_menu": STAGE_MENU,
        "samples": samples,
        "error_form": error_form,
        "next_url": request.get_full_path(),
    })
