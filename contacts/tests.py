from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Connection, Contact, parse_tags

TODAY = date(2026, 11, 14)
EARLIER = date(2026, 10, 1)


def make_user(username):
    return get_user_model().objects.create_user(username, password="Contacts-Test-Pass-731!")


class ParseTagsTests(TestCase):
    def test_normalizes_and_dedupes(self):
        self.assertEqual(parse_tags(" , ,Finance,finance , Alumni"), ["finance", "alumni"])
        self.assertEqual(parse_tags(""), [])


class StageRuleTests(TestCase):
    def setUp(self):
        self.user = make_user("alice")
        self.contact = Contact.objects.create(owner=self.user, name="Amy Chen", last_contact_date=EARLIER)

    def test_new_contact_defaults_to_to_contact(self):
        contact = Contact.objects.create(owner=self.user, name="New Person")
        self.assertEqual(contact.stage, "to_contact")
        self.assertIsNone(contact.last_contact_date)

    def test_moving_to_in_conversation_sets_today(self):
        self.assertTrue(self.contact.change_stage("in_conversation", today=TODAY))
        self.assertEqual(self.contact.last_contact_date, TODAY)

    def test_moving_to_met_sets_today(self):
        self.assertTrue(self.contact.change_stage("met", today=TODAY))
        self.assertEqual(self.contact.last_contact_date, TODAY)

    def test_other_stage_keeps_date(self):
        self.assertTrue(self.contact.change_stage("meeting_set", today=TODAY))
        self.assertEqual(self.contact.last_contact_date, EARLIER)

    def test_same_stage_keeps_date(self):
        self.contact.stage = "met"
        self.assertFalse(self.contact.change_stage("met", today=TODAY))
        self.assertEqual(self.contact.last_contact_date, EARLIER)

    def test_met_inactive_met_updates_date(self):
        self.contact.stage = "met"
        self.contact.change_stage("inactive", today=TODAY)
        self.assertEqual(self.contact.last_contact_date, EARLIER)
        self.contact.change_stage("met", today=TODAY)
        self.assertEqual(self.contact.last_contact_date, TODAY)


class ConnectionTests(TestCase):
    def setUp(self):
        self.alice = make_user("alice")
        self.a = Contact.objects.create(owner=self.alice, name="A")
        self.b = Contact.objects.create(owner=self.alice, name="B")
        self.c = Contact.objects.create(owner=self.alice, name="C")

    def test_deleting_contact_removes_connections_both_directions(self):
        Connection.objects.create(owner=self.alice, from_contact=self.a, to_contact=self.b)
        Connection.objects.create(owner=self.alice, from_contact=self.c, to_contact=self.a)
        Connection.objects.create(owner=self.alice, from_contact=self.b, to_contact=self.c)
        self.assertEqual(self.a.connection_count(), 2)
        self.a.delete()
        self.assertEqual(list(Connection.objects.values_list("from_contact__name", "to_contact__name")), [("B", "C")])

    def test_clean_rejects_other_users_contact(self):
        bob_contact = Contact.objects.create(owner=make_user("bob"), name="Bob's")
        connection = Connection(owner=self.alice, from_contact=self.a, to_contact=bob_contact)
        with self.assertRaises(ValidationError):
            connection.clean()


class SubtitleTests(TestCase):
    def test_subtitle_combines_role_and_company(self):
        user = make_user("alice")
        self.assertEqual(Contact(owner=user, name="x", role="PM", company="Google").subtitle, "PM at Google")
        self.assertEqual(Contact(owner=user, name="x", company="Google").subtitle, "Google")
        self.assertEqual(Contact(owner=user, name="x", role="PM").subtitle, "PM")
        self.assertEqual(Contact(owner=user, name="x").subtitle, "")


class TagTests(TestCase):
    def test_set_tags_reuses_owner_tags_and_builds_tag_string(self):
        user = make_user("alice")
        first = Contact.objects.create(owner=user, name="A")
        second = Contact.objects.create(owner=user, name="B")
        first.set_tags(["finance", "alumni"])
        second.set_tags(["finance"])
        self.assertEqual(first.tag_string, "alumni, finance")
        self.assertEqual(user.contact_tags.count(), 2)
