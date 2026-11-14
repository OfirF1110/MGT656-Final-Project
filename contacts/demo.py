"""Fake sample contacts for the grader accounts (#25). Used by `python manage.py seed`.

Everything here is invented: people, notes and LinkedIn handles (all `offerchat-demo-*`).
Employers are real, well-known firms so the app looks like a real recruiting network.
"""
from datetime import timedelta

from django.utils import timezone

from .models import Connection, Contact, Stage

# days_ago: how long ago the last contact was, relative to the day the seed runs (None = never).
DEMO_CONTACTS = [
    {
        "name": "Maya Okafor", "company": "Goldman Sachs", "role": "Vice President",
        "stage": Stage.MET, "days_ago": 4, "tags": ["finance", "alumni"],
        "linkedin_url": "https://www.linkedin.com/in/offerchat-demo-maya-okafor",
        "notes": "Met at the alumni finance night. Interested in my TMT background; email after Thanksgiving.",
    },
    {
        "name": "Daniel Reyes", "company": "McKinsey & Company", "role": "Engagement Manager",
        "stage": Stage.IN_CONVERSATION, "days_ago": 2, "tags": ["consulting"],
        "notes": "Two calls so far. Offered to review my case-interview prep next week.",
    },
    {
        "name": "Priya Raman", "company": "Google", "role": "Product Manager",
        "stage": Stage.AWAITING_REPLY, "days_ago": None, "tags": ["tech", "product"],
        "notes": "Sent a coffee chat request through the alumni directory.",
    },
    {
        "name": "Jonah Weiss", "company": "Stripe", "role": "Software Engineer",
        "stage": Stage.MEETING_SET, "days_ago": 6, "tags": ["tech", "referral"],
        "linkedin_url": "https://www.linkedin.com/in/offerchat-demo-jonah-weiss",
        "notes": "Coffee booked for Thursday. Ask about the payments team and referral timing.",
    },
    {
        "name": "Elena Novak", "company": "Bain & Company", "role": "Associate Consultant",
        "stage": Stage.TO_CONTACT, "days_ago": None, "tags": ["consulting"],
        "notes": "Classmate's former teammate. Reach out before the Bain info session.",
    },
    {
        "name": "Samuel Adeyemi", "company": "BlackRock", "role": "Analyst",
        "stage": Stage.IN_CONVERSATION, "days_ago": 9, "tags": ["finance"],
        "notes": "",
    },
    {
        "name": "Hannah Lindqvist", "company": "Boston Consulting Group", "role": "Project Leader",
        "stage": Stage.AWAITING_REPLY, "days_ago": 12, "tags": ["consulting", "alumni"],
        "notes": "Followed up after the BCG networking reception.",
    },
    {
        "name": "Marcus Bell", "company": "Citadel", "role": "Recruiter",
        "stage": Stage.INACTIVE, "days_ago": 120, "tags": ["finance"],
        "notes": "Role filled for this cycle. Check back next fall.",
    },
]

# (from name, to name, relationship)
DEMO_CONNECTIONS = [
    ("Maya Okafor", "Jonah Weiss", Connection.Relationship.INTRODUCED_ME),
    ("Hannah Lindqvist", "Maya Okafor", Connection.Relationship.CLASSMATE),
]


def seed_demo_contacts(user, today=None):
    """Add any missing demo contacts and connections for user. Returns how many contacts were created.

    Safe to run repeatedly: a contact that already exists (same owner and name) is left exactly as it is,
    so a second run adds nothing and never overwrites what a grader changed.
    """
    today = today or timezone.localdate()
    created_count = 0
    by_name = {}
    # Created last-to-first so the list (most recently updated first) opens on DEMO_CONTACTS[0].
    for item in reversed(DEMO_CONTACTS):
        days_ago = item["days_ago"]
        contact, created = Contact.objects.get_or_create(
            owner=user,
            name=item["name"],
            defaults={
                "company": item["company"],
                "role": item["role"],
                "stage": item["stage"],
                "notes": item["notes"],
                "linkedin_url": item.get("linkedin_url", ""),
                "last_contact_date": None if days_ago is None else today - timedelta(days=days_ago),
            },
        )
        if created:
            contact.set_tags(item["tags"])
            created_count += 1
        by_name[item["name"]] = contact
    for from_name, to_name, relationship in DEMO_CONNECTIONS:
        Connection.objects.get_or_create(
            owner=user, from_contact=by_name[from_name], to_contact=by_name[to_name],
            defaults={"relationship": relationship},
        )
    return created_count
