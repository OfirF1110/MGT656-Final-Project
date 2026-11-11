import uuid

from django.db import models
from django.utils import timezone


class Visit(models.Model):
    """One row per visitor of the A/B page.

    The unique visitor_id guarantees at most one impression per visitor.
    clicked_at stays empty until the visitor clicks, so at most one click is
    counted per visitor as well.
    """

    KUDOS = "kudos"
    THANKS = "thanks"
    VARIANT_CHOICES = [(KUDOS, "kudos"), (THANKS, "thanks")]

    visitor_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    variant = models.CharField(max_length=6, choices=VARIANT_CHOICES)
    impression_at = models.DateTimeField(default=timezone.now)
    clicked_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        clicked = "clicked" if self.clicked_at else "no click"
        return f"{self.variant} ({clicked})"
