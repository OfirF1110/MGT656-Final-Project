import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q
from django.db.models.functions import Lower
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.cache import patch_vary_headers
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import ContactForm
from .models import STAGE_MENU, Contact, Stage


def is_htmx(request):
    """True for htmx fragment requests. History restores need the full page."""
    return (
        request.headers.get("HX-Request") == "true"
        and request.headers.get("HX-History-Restore-Request") != "true"
    )


def get_contact_or_404(request, pk):
    """Every contact lookup goes through here: other users' contacts are a 404."""
    return get_object_or_404(Contact, pk=pk, owner=request.user)


def _connections(contact):
    """[(other_contact, relationship_label)] for both directions."""
    pairs = [(c.to_contact, c.get_relationship_display()) for c in contact.connections_out.select_related("to_contact")]
    pairs += [(c.from_contact, c.get_relationship_display()) for c in contact.connections_in.select_related("from_contact")]
    return sorted(pairs, key=lambda pair: pair[0].name.lower())


SORTS = {
    "updated": ("Recently updated", ["-updated_at", "-id"]),
    "name": ("Name", ["name_lower", "id"]),
    "last_contact": ("Last contact", [F("last_contact_date").desc(nulls_last=True), "name_lower", "id"]),
}


def sort_contacts(queryset, sort):
    """Order by one of SORTS; unknown values fall back to recently updated.
    name_lower is annotated (not an order_by expression) so it works with distinct() on Postgres."""
    _, ordering = SORTS.get(sort, SORTS["updated"])
    return queryset.annotate(name_lower=Lower("name")).order_by(*ordering)


def filter_contacts(queryset, q, stage):
    """Search name, company and tag names (case-insensitive, partial) and filter by stage."""
    if q:
        queryset = queryset.filter(
            Q(name__icontains=q) | Q(company__icontains=q) | Q(tags__name__icontains=q)
        ).distinct()
    if stage in Stage.values:
        queryset = queryset.filter(stage=stage)
    return queryset


@login_required
def contact_list(request):
    q = request.GET.get("q", "").strip()
    stage = request.GET.get("stage", "")
    stage = stage if stage in Stage.values else ""
    sort = request.GET.get("sort", "updated")
    sort = sort if sort in SORTS else "updated"
    mine = Contact.objects.filter(owner=request.user)
    contacts = list(sort_contacts(filter_contacts(mine, q, stage), sort).prefetch_related("tags"))
    template = "contacts/_results.html" if is_htmx(request) else "contacts/list.html"
    response = render(request, template, {
        "contacts": contacts,
        "count": len(contacts),
        "total": mine.count(),
        "q": q,
        "stage": stage,
        "stage_label": Stage(stage).label if stage else "",
        "is_filtered": bool(q or stage),
        "is_htmx": is_htmx(request),
        "stage_choices": Stage.choices,
        "sort": sort,
        "sort_choices": [(key, label) for key, (label, _) in SORTS.items()],
        "stage_menu": STAGE_MENU,
        "next_url": request.get_full_path(),
        "nav_active": "contacts",
    })
    patch_vary_headers(response, ["HX-Request"])
    return response


@login_required
def contact_create(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        contact = form.save_for(request.user)
        messages.success(request, "Contact added")
        return redirect(contact)
    return render(request, "contacts/form.html", {"form": form, "nav_active": "contacts"})


@login_required
def contact_detail(request, pk):
    contact = get_contact_or_404(request, pk)
    return render(request, "contacts/detail.html", {
        "contact": contact,
        "connections": _connections(contact),
        "stage_menu": STAGE_MENU,
        "nav_active": "contacts",
    })


@login_required
def contact_edit(request, pk):
    contact = get_contact_or_404(request, pk)
    form = ContactForm(request.POST or None, instance=contact)
    if request.method == "POST" and form.is_valid():
        form.save_for(request.user)
        messages.success(request, "Changes saved")
        return redirect(contact)
    return render(request, "contacts/form.html", {"form": form, "contact": contact, "nav_active": "contacts"})


def _safe_next(request, fallback):
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}, require_https=request.is_secure()):
        return next_url
    return fallback


@login_required
@require_POST
def contact_stage(request, pk):
    contact = get_contact_or_404(request, pk)
    new_stage = request.POST.get("stage", "")
    if new_stage not in Stage.values:
        return HttpResponseBadRequest("Unknown stage")
    if contact.change_stage(new_stage):
        contact.save()
    if is_htmx(request):
        in_row = request.POST.get("context") == "row"
        response = render(request, "contacts/_row.html" if in_row else "contacts/_stage_panel.html", {
            "contact": contact,
            "stage_menu": STAGE_MENU,
            "next_url": _safe_next(request, contact.get_absolute_url()),
        })
        response["HX-Trigger"] = json.dumps({"toast": "Stage updated"})
        return response
    messages.success(request, "Stage updated")
    return redirect(_safe_next(request, contact.get_absolute_url()))


@login_required
def contact_delete(request, pk):
    contact = get_contact_or_404(request, pk)
    if request.method == "POST":
        name = contact.name
        contact.delete()
        messages.success(request, f"{name} deleted")
        return redirect("contacts:list")
    return render(request, "contacts/confirm_delete.html", {
        "contact": contact,
        "connection_count": contact.connection_count(),
        "nav_active": "contacts",
    })
