from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods

from .forms import NotesForm
from .services import SummaryError, summarize_notes

@sensitive_post_parameters("notes")
@login_required
@never_cache
@require_http_methods(["GET", "POST"])
def summarize(request):
    form = NotesForm(request.POST if request.method == "POST" else None)
    summary = ""
    error = ""
    if request.method == "POST" and form.is_valid():
        try:
            summary = summarize_notes(form.cleaned_data["notes"])
        except SummaryError as exc:
            error = str(exc)
    return render(request, "summaries/form.html", {
        "form": form, "summary": summary, "error": error, "nav_active": "summaries",
    })
