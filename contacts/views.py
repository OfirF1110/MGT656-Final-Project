from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ContactForm
from .models import STAGE_MENU, Contact


def get_contact_or_404(request, pk):
    """Every contact lookup goes through here: other users' contacts are a 404."""
    return get_object_or_404(Contact, pk=pk, owner=request.user)


def _connections(contact):
    """[(other_contact, relationship_label)] for both directions."""
    pairs = [(c.to_contact, c.get_relationship_display()) for c in contact.connections_out.select_related("to_contact")]
    pairs += [(c.from_contact, c.get_relationship_display()) for c in contact.connections_in.select_related("from_contact")]
    return sorted(pairs, key=lambda pair: pair[0].name.lower())


@login_required
def contact_list(request):
    raise Http404  # Replaced in Task 4.


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


@login_required
def contact_stage(request, pk):
    raise Http404  # Replaced in Task 5.


@login_required
def contact_delete(request, pk):
    raise Http404  # Replaced in Task 5.
