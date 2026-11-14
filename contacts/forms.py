from urllib.parse import urlsplit, urlunsplit

from django import forms

from .models import TAG_MAX_LENGTH, Contact, Stage, parse_tags

LINKEDIN_ERROR = "Enter a LinkedIn profile link, like linkedin.com/in/yourname"


class ContactForm(forms.ModelForm):
    name = forms.CharField(max_length=120, error_messages={"required": "Enter a name"})
    stage = forms.ChoiceField(choices=Stage.choices, initial=Stage.TO_CONTACT)
    linkedin_url = forms.URLField(
        required=False, max_length=300, assume_scheme="https", label="LinkedIn profile",
        error_messages={"invalid": LINKEDIN_ERROR},
    )
    tags = forms.CharField(required=False, help_text="Separate tags with commas")

    class Meta:
        model = Contact
        fields = ["name", "company", "role", "linkedin_url", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial.setdefault("stage", self.instance.stage)
            self.initial.setdefault("tags", self.instance.tag_string)
        # Placeholders only where they show a format, so empty fields never look filled in.
        self.fields["name"].widget.attrs["autocomplete"] = "off"
        self.fields["linkedin_url"].widget.attrs["placeholder"] = "linkedin.com/in/amychen"
        self.fields["tags"].widget.attrs["placeholder"] = "finance, alumni"

    def clean_linkedin_url(self):
        url = self.cleaned_data["linkedin_url"]
        if not url:
            return ""
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
        if host != "linkedin.com" and not host.endswith(".linkedin.com"):
            raise forms.ValidationError(LINKEDIN_ERROR)
        return urlunsplit(("https", host, parts.path, parts.query, ""))

    def clean_tags(self):
        names = parse_tags(self.cleaned_data["tags"])
        if any(len(name) > TAG_MAX_LENGTH for name in names):
            raise forms.ValidationError(f"Keep each tag under {TAG_MAX_LENGTH} characters")
        return names

    def save_for(self, owner):
        """Save the contact for owner, applying the stage rule and tags."""
        contact = super().save(commit=False)
        if contact.pk is None:
            contact.owner = owner
        contact.change_stage(self.cleaned_data["stage"])
        contact.save()
        contact.set_tags(self.cleaned_data["tags"])
        return contact
