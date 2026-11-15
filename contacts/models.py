from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Stage(models.TextChoices):
    TO_CONTACT = "to_contact", "To contact"
    AWAITING_REPLY = "awaiting_reply", "Awaiting reply"
    IN_CONVERSATION = "in_conversation", "In conversation"
    MEETING_SET = "meeting_set", "Meeting set"
    MET = "met", "Met"
    INACTIVE = "inactive", "Inactive"


# Moving into one of these stages records today as the last contact date (#10).
TOUCH_STAGES = {Stage.IN_CONVERSATION, Stage.MET}

# Groups shown in the stage menu, in order.
STAGE_MENU = [
    ("Not started", [Stage.TO_CONTACT]),
    ("Active", [Stage.AWAITING_REPLY, Stage.IN_CONVERSATION, Stage.MEETING_SET]),
    ("Done", [Stage.MET, Stage.INACTIVE]),
]

TAG_MAX_LENGTH = 40


def parse_tags(raw):
    """Turn "Finance, alumni, finance" into ["finance", "alumni"]."""
    names = []
    for part in (raw or "").split(","):
        name = part.strip().lower()
        if name and name not in names:
            names.append(name)
    return names


class Tag(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contact_tags")
    name = models.CharField(max_length=TAG_MAX_LENGTH)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["owner", "name"], name="unique_tag_per_owner")]

    def __str__(self):
        return self.name


class Contact(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contacts")
    name = models.CharField(max_length=120)
    company = models.CharField(max_length=120, blank=True)
    role = models.CharField(max_length=120, blank=True)
    linkedin_url = models.URLField(max_length=300, blank=True)
    notes = models.TextField(blank=True)
    stage = models.CharField(max_length=20, choices=Stage.choices, default=Stage.TO_CONTACT)
    # Written only by change_stage() (and later by meeting logging), never edited in a form.
    last_contact_date = models.DateField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="contacts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-id"]
        constraints = [
            models.CheckConstraint(condition=models.Q(stage__in=Stage.values), name="contact_stage_valid"),
        ]
        indexes = [
            models.Index(fields=["owner", "stage"], name="contact_owner_stage_idx"),
            models.Index(fields=["owner", "updated_at"], name="contact_owner_updated_idx"),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("contacts:detail", args=[self.pk])

    def change_stage(self, new_stage, today=None):
        """Set the stage. Moving into In conversation or Met sets last contact to today.

        Only mutates the instance; the caller saves. Kept out of save() on purpose:
        meeting logging (#11) sets Met with the meeting's date, not today.
        Returns True if the stage actually changed.
        """
        if new_stage == self.stage:
            return False
        self.stage = new_stage
        if new_stage in TOUCH_STAGES:
            self.last_contact_date = today or timezone.localdate()
        return True

    def set_tags(self, names):
        tags = [Tag.objects.get_or_create(owner=self.owner, name=name)[0] for name in names]
        self.tags.set(tags)

    @property
    def tag_string(self):
        return ", ".join(tag.name for tag in self.tags.all())

    @property
    def subtitle(self):
        if self.role and self.company:
            return f"{self.role} at {self.company}"
        return self.role or self.company

    def connection_count(self):
        return self.connections_out.count() + self.connections_in.count()


class Connection(models.Model):
    class Relationship(models.TextChoices):
        COLLEAGUE = "colleague", "Colleague"
        INTRODUCED_ME = "introduced_me", "Introduced me"
        CLASSMATE = "classmate", "Classmate"
        KNOWS = "knows", "Knows"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contact_connections")
    from_contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name="connections_out")
    to_contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name="connections_in")
    relationship = models.CharField(max_length=20, choices=Relationship.choices, default=Relationship.KNOWS)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=~models.Q(from_contact=models.F("to_contact")), name="connection_not_self"),
            models.UniqueConstraint(fields=["from_contact", "to_contact"], name="unique_connection_pair"),
        ]

    def __str__(self):
        return f"{self.from_contact} → {self.to_contact}"

    def clean(self):
        if self.from_contact.owner_id != self.owner_id or self.to_contact.owner_id != self.owner_id:
            raise ValidationError("Both contacts must belong to you.")
