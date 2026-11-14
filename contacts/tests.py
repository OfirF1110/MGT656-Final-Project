from datetime import date
from unittest.mock import patch

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


class LoggedInTestCase(TestCase):
    def setUp(self):
        self.alice = make_user("alice")
        self.client.force_login(self.alice)


VALID = {
    "name": "Amy Chen",
    "company": "Goldman Sachs",
    "role": "VP",
    "tags": "Finance, alumni",
    "notes": "Met at SOM",
    "linkedin_url": "linkedin.com/in/amychen",
    "stage": "to_contact",
}


class CreateEditTests(LoggedInTestCase):
    def test_create_contact_with_all_fields(self):
        response = self.client.post("/contacts/new/", VALID, follow=True)
        contact = Contact.objects.get()
        self.assertRedirects(response, f"/contacts/{contact.pk}/")
        self.assertEqual(contact.owner, self.alice)
        self.assertEqual((contact.company, contact.role, contact.notes), ("Goldman Sachs", "VP", "Met at SOM"))
        self.assertEqual(contact.stage, "to_contact")
        self.assertEqual(contact.linkedin_url, "https://linkedin.com/in/amychen")
        self.assertEqual(set(contact.tags.values_list("name", flat=True)), {"finance", "alumni"})
        self.assertContains(response, "Contact added")

    def test_missing_name_shows_error_and_creates_nothing(self):
        for name in ("", "   "):
            response = self.client.post("/contacts/new/", {**VALID, "name": name})
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Enter a name")
            self.assertContains(response, 'value="Goldman Sachs"')
        self.assertEqual(Contact.objects.count(), 0)

    def test_create_with_met_sets_last_contact_today(self):
        with patch("contacts.models.timezone.localdate", return_value=TODAY):
            self.client.post("/contacts/new/", {**VALID, "stage": "met"})
        contact = Contact.objects.get()
        self.assertEqual((contact.stage, contact.last_contact_date), ("met", TODAY))

    def test_edit_without_stage_change_keeps_date(self):
        contact = Contact.objects.create(owner=self.alice, name="Amy Chen", stage="met", last_contact_date=EARLIER)
        response = self.client.post(f"/contacts/{contact.pk}/edit/", {**VALID, "stage": "met", "notes": "Changed"}, follow=True)
        self.assertRedirects(response, f"/contacts/{contact.pk}/")
        contact.refresh_from_db()
        self.assertEqual((contact.notes, contact.last_contact_date), ("Changed", EARLIER))
        self.assertContains(response, "Changes saved")

    def test_edit_to_in_conversation_sets_today(self):
        contact = Contact.objects.create(owner=self.alice, name="Amy Chen", last_contact_date=EARLIER)
        with patch("contacts.models.timezone.localdate", return_value=TODAY):
            self.client.post(f"/contacts/{contact.pk}/edit/", {**VALID, "stage": "in_conversation"})
        contact.refresh_from_db()
        self.assertEqual((contact.stage, contact.last_contact_date), ("in_conversation", TODAY))

    def test_edit_form_shows_existing_tags(self):
        contact = Contact.objects.create(owner=self.alice, name="Amy Chen")
        contact.set_tags(["finance", "alumni"])
        self.assertContains(self.client.get(f"/contacts/{contact.pk}/edit/"), 'value="alumni, finance"')

    def test_linkedin_validation(self):
        for bad in ("https://linkedin.com.evil.com/in/x", "notlinkedin.com/in/x", "https://example.com/x"):
            response = self.client.post("/contacts/new/", {**VALID, "linkedin_url": bad})
            self.assertContains(response, "Enter a LinkedIn profile link, like linkedin.com/in/yourname")
        self.assertEqual(Contact.objects.count(), 0)
        self.client.post("/contacts/new/", {**VALID, "linkedin_url": "HTTP://WWW.LinkedIn.com/in/x"})
        self.assertEqual(Contact.objects.count(), 1)

    def test_long_tag_is_form_error(self):
        response = self.client.post("/contacts/new/", {**VALID, "tags": "a" * 41})
        self.assertContains(response, "Keep each tag under 40 characters")
        self.assertEqual(Contact.objects.count(), 0)

    def test_detail_shows_fields_and_hides_empty_connections(self):
        contact = Contact.objects.create(owner=self.alice, name="Amy Chen", role="VP", company="Goldman Sachs",
                                         linkedin_url="https://www.linkedin.com/in/amychen")
        contact.set_tags(["finance"])
        response = self.client.get(f"/contacts/{contact.pk}/")
        self.assertContains(response, "Amy Chen")
        self.assertContains(response, "VP at Goldman Sachs")
        self.assertContains(response, "finance")
        self.assertContains(response, ">linkedin.com/in/amychen<")
        self.assertNotContains(response, "Connections")
        other = Contact.objects.create(owner=self.alice, name="Jin Lee")
        Connection.objects.create(owner=self.alice, from_contact=contact, to_contact=other)
        self.assertContains(self.client.get(f"/contacts/{contact.pk}/"), "Connections")

    def test_anonymous_redirected_to_login(self):
        self.client.logout()
        self.assertRedirects(self.client.get("/contacts/new/"), "/login/?next=/contacts/new/")


class ListSearchTests(LoggedInTestCase):
    def setUp(self):
        super().setUp()
        self.amy = Contact.objects.create(owner=self.alice, name="Amy Chen", company="Goldman Sachs", stage="met")
        self.amy.set_tags(["finance"])
        self.david = Contact.objects.create(owner=self.alice, name="David Roy", company="McKinsey")
        self.david.set_tags(["consulting"])
        bob = make_user("bob")
        Contact.objects.create(owner=bob, name="Goldie Hawn", company="Gold Films")

    def test_list_shows_only_own_contacts(self):
        response = self.client.get("/contacts/")
        self.assertContains(response, "Amy Chen")
        self.assertContains(response, "David Roy")
        self.assertNotContains(response, "Goldie")
        self.assertContains(response, "2 people")

    def test_partial_case_insensitive_search_by_company(self):
        for q in ("gold", "GOLD"):
            response = self.client.get("/contacts/", {"q": q})
            self.assertContains(response, "Amy Chen")
            self.assertNotContains(response, "David Roy")
            self.assertNotContains(response, "Goldie")
            self.assertContains(response, "1 contact matches")

    def test_search_by_name_and_tag(self):
        response = self.client.get("/contacts/", {"q": "dav"})
        self.assertContains(response, "David Roy")
        self.assertNotContains(response, "Amy Chen")
        response = self.client.get("/contacts/", {"q": "consult"})
        self.assertContains(response, "David Roy")
        self.assertNotContains(response, "Amy Chen")

    def test_search_matching_several_tags_lists_contact_once(self):
        self.amy.set_tags(["finance", "fintech"])
        response = self.client.get("/contacts/", {"q": "fin"})
        self.assertEqual(response.content.decode().count(f'id="contact-{self.amy.pk}"'), 1)

    def test_stage_filter_combines_with_search(self):
        response = self.client.get("/contacts/", {"stage": "met"})
        self.assertContains(response, "Amy Chen")
        self.assertNotContains(response, "David Roy")
        response = self.client.get("/contacts/", {"stage": "met", "q": "roy"})
        self.assertNotContains(response, "David Roy")
        self.assertContains(response, "No contacts match")

    def test_invalid_stage_is_ignored(self):
        response = self.client.get("/contacts/", {"stage": "bogus"})
        self.assertContains(response, "Amy Chen")
        self.assertContains(response, "David Roy")

    def test_no_results_message_escapes_query(self):
        response = self.client.get("/contacts/", {"q": '<script>x"'})
        self.assertContains(response, "No contacts match &quot;&lt;script&gt;x&quot;&quot;")
        self.assertNotContains(response, "<script>x")

    def test_empty_state_for_new_user(self):
        self.client.force_login(make_user("carol"))
        response = self.client.get("/contacts/")
        self.assertContains(response, "Add your first contact")
        self.assertContains(response, "0 people")

    def test_sidebar_shows_contact_count(self):
        response = self.client.get("/contacts/")
        self.assertContains(response, '<span class="app-nav-count">2</span>')


class LandingRedirectTests(TestCase):
    def test_login_redirects_to_contacts(self):
        make_user("alice")
        response = self.client.post("/login/", {"username": "alice", "password": "Contacts-Test-Pass-731!"})
        self.assertRedirects(response, "/contacts/")

    def test_home_redirects_logged_in_user(self):
        self.client.force_login(make_user("alice"))
        self.assertRedirects(self.client.get("/"), "/contacts/")
        self.client.logout()
        self.assertEqual(self.client.get("/").status_code, 200)
