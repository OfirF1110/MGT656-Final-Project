from django import forms

class NotesForm(forms.Form):
    notes = forms.CharField(
        label="Meeting notes", max_length=12000,
        error_messages={"required": "Paste some notes first"},
        widget=forms.Textarea(attrs={"rows": 10, "class": "form-control"}),
        help_text="Up to 12,000 characters. Notes are sent to the AI provider when you submit.",
    )
