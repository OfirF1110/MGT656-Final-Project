from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase

from .models import Connection, Contact, Stage, parse_tags

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


class StageViewTests(LoggedInTestCase):
    def setUp(self):
        super().setUp()
        self.contact = Contact.objects.create(owner=self.alice, name="Amy Chen", last_contact_date=EARLIER)
        self.url = f"/contacts/{self.contact.pk}/stage/"

    def test_stage_post_to_met_sets_today_and_redirects_to_next(self):
        with patch("contacts.models.timezone.localdate", return_value=TODAY):
            response = self.client.post(self.url, {"stage": "met", "next": "/contacts/?q=a"})
        self.assertRedirects(response, "/contacts/?q=a", fetch_redirect_response=False)
        self.contact.refresh_from_db()
        self.assertEqual((self.contact.stage, self.contact.last_contact_date), ("met", TODAY))

    def test_unknown_stage_returns_400_and_changes_nothing(self):
        for data in ({"stage": "bogus"}, {}):
            self.assertEqual(self.client.post(self.url, data).status_code, 400)
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.stage, "to_contact")

    def test_external_next_falls_back_to_detail(self):
        response = self.client.post(self.url, {"stage": "awaiting_reply", "next": "https://evil.example/"})
        self.assertRedirects(response, f"/contacts/{self.contact.pk}/", fetch_redirect_response=False)

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)


class DeleteTests(LoggedInTestCase):
    def setUp(self):
        super().setUp()
        self.amy = Contact.objects.create(owner=self.alice, name="Amy Chen")
        self.jin = Contact.objects.create(owner=self.alice, name="Jin Lee")
        Connection.objects.create(owner=self.alice, from_contact=self.amy, to_contact=self.jin)
        self.url = f"/contacts/{self.amy.pk}/delete/"

    def test_get_shows_confirmation_with_connection_count_and_deletes_nothing(self):
        response = self.client.get(self.url)
        self.assertContains(response, "Delete Amy Chen?")
        self.assertContains(response, "This also removes 1 connection.")
        self.assertEqual(Contact.objects.count(), 2)

    def test_post_deletes_contact_and_connections(self):
        response = self.client.post(self.url, follow=True)
        self.assertRedirects(response, "/contacts/")
        self.assertContains(response, "Amy Chen deleted")
        self.assertFalse(Contact.objects.filter(pk=self.amy.pk).exists())
        self.assertEqual(Connection.objects.count(), 0)
        self.assertTrue(Contact.objects.filter(pk=self.jin.pk).exists())


class PrivacyTests(TestCase):
    def test_other_users_contact_is_404_everywhere(self):
        alice = make_user("alice")
        contact = Contact.objects.create(owner=alice, name="Amy Chen", stage="met")
        self.client.force_login(make_user("bob"))
        base = f"/contacts/{contact.pk}"
        requests = [
            ("get", f"{base}/"),
            ("get", f"{base}/edit/"),
            ("post", f"{base}/edit/"),
            ("get", f"{base}/delete/"),
            ("post", f"{base}/delete/"),
            ("post", f"{base}/stage/"),
        ]
        for method, url in requests:
            data = {**VALID, "name": "Hacked", "stage": "inactive"} if method == "post" else None
            response = getattr(self.client, method)(url, data)
            self.assertEqual(response.status_code, 404, f"{method.upper()} {url}")
        contact.refresh_from_db()
        self.assertEqual((contact.name, contact.stage), ("Amy Chen", "met"))


HX = {"HTTP_HX_REQUEST": "true"}


class HtmxTests(LoggedInTestCase):
    def setUp(self):
        super().setUp()
        self.amy = Contact.objects.create(owner=self.alice, name="Amy Chen", company="Goldman Sachs")
        Contact.objects.create(owner=self.alice, name="David Roy", company="McKinsey")

    def test_list_htmx_returns_fragment(self):
        response = self.client.get("/contacts/", {"q": "gold"}, **HX)
        html = response.content.decode()
        self.assertNotIn("<html", html)
        self.assertIn("Amy Chen", html)
        self.assertNotIn("David Roy", html)
        self.assertIn("HX-Request", response["Vary"])

    def test_full_list_page_also_varies_on_htmx_header(self):
        response = self.client.get("/contacts/")
        self.assertIn("<html", response.content.decode())
        self.assertIn("HX-Request", response["Vary"])

    def test_stage_htmx_returns_row_with_toast_trigger(self):
        response = self.client.post(f"/contacts/{self.amy.pk}/stage/", {"stage": "met", "context": "row"}, **HX)
        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("<html", html)
        self.assertIn(f'id="contact-{self.amy.pk}"', html)
        self.assertIn('aria-label="Change stage, currently Met"', html)
        self.assertIn("Stage updated", response["HX-Trigger"])
        self.assertNotIn("Stage updated", self.client.get("/contacts/").content.decode())

    def test_stage_htmx_panel_context_returns_panel(self):
        response = self.client.post(f"/contacts/{self.amy.pk}/stage/", {"stage": "met", "context": "panel"}, **HX)
        self.assertContains(response, f'id="stage-panel-{self.amy.pk}"')
        self.assertNotContains(response, "contact-row")

    def test_htmx_post_passes_csrf_with_header(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.alice)
        client.get("/contacts/")
        token = client.cookies["csrftoken"].value
        url = f"/contacts/{self.amy.pk}/stage/"
        ok = client.post(url, {"stage": "met", "context": "row"}, HTTP_X_CSRFTOKEN=token, **HX)
        self.assertEqual(ok.status_code, 200)
        refused = client.post(url, {"stage": "inactive", "context": "row"}, **HX)
        self.assertEqual(refused.status_code, 403)

    def test_list_page_wires_htmx_attributes(self):
        html = self.client.get("/contacts/").content.decode()
        self.assertIn('hx-target="#contact-results"', html)
        self.assertIn('hx-post="/contacts/', html)

    def test_history_restore_gets_full_page(self):
        response = self.client.get("/contacts/", HTTP_HX_REQUEST="true", HTTP_HX_HISTORY_RESTORE_REQUEST="true")
        self.assertIn("<html", response.content.decode())


class PolishTests(LoggedInTestCase):
    def test_detail_has_phone_actions_with_delete(self):
        contact = Contact.objects.create(owner=self.alice, name="Amy Chen")
        html = self.client.get(f"/contacts/{contact.pk}/").content.decode()
        start = html.index('class="detail-mobile-actions"')
        block = html[start:html.index("</div>", start)]
        self.assertIn(f'href="/contacts/{contact.pk}/delete/"', block)
        self.assertIn(f'href="/contacts/{contact.pk}/edit/"', block)

    def test_stage_menu_has_sheet_title_for_phones(self):
        contact = Contact.objects.create(owner=self.alice, name="Amy Chen")
        self.assertContains(self.client.get("/contacts/"), "Change stage for Amy Chen")

    def test_no_results_with_stage_filter_mentions_stage(self):
        Contact.objects.create(owner=self.alice, name="Amy Chen", company="Goldman Sachs")
        response = self.client.get("/contacts/", {"q": "gold", "stage": "met"})
        self.assertContains(response, "No contacts match &quot;gold&quot; in Met")

    def test_name_field_has_no_example_value(self):
        html = self.client.get("/contacts/new/").content.decode()
        name_input = html[html.index('id="id_name"') - 200: html.index('id="id_name"') + 50]
        self.assertNotIn("placeholder", name_input)


class ReviewFixTests(LoggedInTestCase):
    def setUp(self):
        super().setUp()
        Contact.objects.create(owner=self.alice, name="Amy Chen", company="Goldman Sachs")

    def test_htmx_history_cache_is_disabled(self):
        html = self.client.get("/contacts/").content.decode()
        self.assertIn('<meta name="htmx-config" content=\'{"historyCacheSize": 0}\'>', html)

    def test_live_region_is_a_short_status_outside_results(self):
        html = self.client.get("/contacts/", {"q": "gold"}).content.decode()
        results = html[html.index('id="contact-results"') - 60: html.index('id="contact-results"') + 60]
        self.assertNotIn("aria-live", results)
        self.assertIn('id="results-status" class="visually-hidden" role="status"', html)
        self.assertLess(html.index('id="results-status"'), html.index('id="contact-results"'))

    def test_htmx_results_update_status_out_of_band(self):
        html = self.client.get("/contacts/", {"q": "gold"}, **HX).content.decode()
        self.assertIn('id="results-status"', html)
        self.assertIn('hx-swap-oob="innerHTML"', html)
        self.assertIn("1 contact matches &quot;gold&quot;", html)
        html = self.client.get("/contacts/", {"q": "zzz"}, **HX).content.decode()
        self.assertIn("No contacts match &quot;zzz&quot;", html[html.index('id="results-status"'):])

    def test_live_search_replaces_url_instead_of_adding_history(self):
        html = self.client.get("/contacts/").content.decode()
        search_input = html[html.index('name="q"'): html.index('name="q"') + 500]
        self.assertIn('hx-replace-url="true"', search_input)
        self.assertNotIn("hx-push-url", html)


class StaticAssetTests(TestCase):
    def test_every_static_reference_in_templates_exists(self):
        import re
        from pathlib import Path

        from django.conf import settings
        from django.contrib.staticfiles import finders

        refs = set()
        for path in Path(settings.BASE_DIR).glob("**/templates/**/*.html"):
            if ".venv" in path.parts or "staticfiles" in path.parts:
                continue
            refs.update(re.findall(r"{%\s*static\s+'([^']+)'\s*%}", path.read_text(encoding="utf-8")))
        self.assertIn("css/theme.css", refs)
        missing = sorted(ref for ref in refs if not finders.find(ref))
        self.assertEqual(missing, [])


class AvatarTests(TestCase):
    def test_initials(self):
        from contacts.templatetags.contacts_ui import initials
        self.assertEqual(initials("Amy Chen"), "AC")
        self.assertEqual(initials("amy van der berg"), "AB")
        self.assertEqual(initials("Madonna"), "M")
        self.assertEqual(initials("李晓明"), "李")
        self.assertEqual(initials("  "), "?")

    def test_tone_is_stable_and_in_palette(self):
        from contacts.templatetags.contacts_ui import AVATAR_TONES, avatar_tone
        self.assertEqual(avatar_tone("Amy Chen"), avatar_tone("Amy Chen"))
        self.assertIn(avatar_tone("Amy Chen"), range(AVATAR_TONES))
        self.assertGreater(len({avatar_tone(n) for n in ["Amy Chen", "David Roy", "Sara Patel", "Jin Lee", "Mark Kim", "Tom Wu"]}), 2)


class ListPolishTests(LoggedInTestCase):
    def setUp(self):
        super().setUp()
        self.amy = Contact.objects.create(owner=self.alice, name="Amy Chen", last_contact_date=date(2026, 11, 10),
                                          linkedin_url="https://www.linkedin.com/in/amychen")
        self.bob = Contact.objects.create(owner=self.alice, name="bob Stone", last_contact_date=None)
        self.cara = Contact.objects.create(owner=self.alice, name="Cara Diaz", last_contact_date=date(2026, 11, 12))

    def names_in_order(self, **params):
        html = self.client.get("/contacts/", params).content.decode()
        names = ["Amy Chen", "bob Stone", "Cara Diaz"]
        return sorted(names, key=lambda n: html.index(f">{n}</a>"))

    def test_rows_show_initials_avatar(self):
        self.assertContains(self.client.get("/contacts/"), '<span class="avatar avatar--tone-')
        self.assertContains(self.client.get("/contacts/"), ">AC</span>")

    def test_sort_by_name_is_case_insensitive(self):
        self.assertEqual(self.names_in_order(sort="name"), ["Amy Chen", "bob Stone", "Cara Diaz"])

    def test_sort_by_last_contact_puts_never_last(self):
        self.assertEqual(self.names_in_order(sort="last_contact"), ["Cara Diaz", "Amy Chen", "bob Stone"])

    def test_unknown_sort_falls_back_to_recently_updated(self):
        self.assertEqual(self.names_in_order(sort="bogus"), self.names_in_order())
        self.assertEqual(self.names_in_order()[0], "Cara Diaz")

    def test_sort_select_keeps_choice_and_drives_htmx(self):
        html = self.client.get("/contacts/", {"sort": "name"}).content.decode()
        select = html[html.index('name="sort"') - 20: html.index('name="sort"') + 400]
        self.assertIn('hx-get="/contacts/"', select)
        self.assertIn('<option value="name" selected>', html)

    def test_row_quick_actions_have_labels_and_linkedin_only_when_present(self):
        html = self.client.get("/contacts/").content.decode()
        self.assertIn('aria-label="Open Amy Chen"', html)
        self.assertIn('aria-label="Amy Chen on LinkedIn"', html)
        self.assertNotIn('aria-label="bob Stone on LinkedIn"', html)


SEED_CREDS = {
    "GRADER_ADMIN_USERNAME": "grader-admin@example.com",
    "GRADER_ADMIN_PASSWORD": "Example-Only-Admin-752!",
    "GRADER_MEMBER_USERNAME": "grader-member@example.com",
    "GRADER_MEMBER_PASSWORD": "Example-Only-Member-981!",
}


@patch.dict("os.environ", SEED_CREDS)
class DemoSeedTests(TestCase):
    def run_seed(self):
        from io import StringIO

        from django.core.management import call_command
        out = StringIO()
        call_command("seed", stdout=out)
        return out.getvalue()

    def graders(self):
        User = get_user_model()
        return [User.objects.get(username=SEED_CREDS[f"GRADER_{r}_USERNAME"]) for r in ("ADMIN", "MEMBER")]

    def snapshot(self):
        from contacts.models import Tag
        return (
            sorted(Contact.objects.values_list("id", "owner_id", "name", "stage")),
            sorted(Tag.objects.values_list("id", "owner_id", "name")),
            sorted(Connection.objects.values_list("id", "from_contact_id", "to_contact_id")),
        )

    def test_seed_creates_demo_contacts_for_both_graders(self):
        from contacts.demo import DEMO_CONTACTS
        output = self.run_seed()
        for grader in self.graders():
            contacts = Contact.objects.filter(owner=grader)
            self.assertEqual(contacts.count(), len(DEMO_CONTACTS))
            self.assertEqual(set(contacts.values_list("stage", flat=True)), set(Stage.values))
            self.assertTrue(grader.contact_tags.exists())
            self.assertGreaterEqual(grader.contact_connections.count(), 2)
            self.assertTrue(contacts.filter(last_contact_date__isnull=False).exists())
        self.assertIn("Demo contacts added: 16", output)
        self.assertNotIn(SEED_CREDS["GRADER_MEMBER_PASSWORD"], output)

    def test_second_run_adds_nothing(self):
        self.run_seed()
        before = self.snapshot()
        output = self.run_seed()
        self.assertEqual(self.snapshot(), before)
        self.assertIn("Demo contacts added: 0", output)

    def test_rerun_keeps_grader_edits(self):
        self.run_seed()
        contact = Contact.objects.filter(owner=self.graders()[1]).first()
        contact.notes = "Edited by a grader"
        contact.stage = "inactive"
        contact.save()
        self.run_seed()
        contact.refresh_from_db()
        self.assertEqual((contact.notes, contact.stage), ("Edited by a grader", "inactive"))

    def test_seed_still_creates_both_accounts(self):
        self.run_seed()
        admin, member = self.graders()
        self.assertTrue(admin.is_superuser)
        self.assertFalse(member.is_superuser)

    def test_other_users_get_no_demo_data_and_keep_theirs(self):
        other = make_user("someone-else")
        Contact.objects.create(owner=other, name="My Real Contact")
        self.run_seed()
        self.assertEqual(list(Contact.objects.filter(owner=other).values_list("name", flat=True)), ["My Real Contact"])

    def test_demo_data_is_clearly_fake(self):
        from contacts.demo import DEMO_CONTACTS
        for item in DEMO_CONTACTS:
            url = item.get("linkedin_url", "")
            self.assertTrue(url == "" or "offerchat-demo" in url, url)

    def test_list_opens_on_the_richest_demo_contact(self):
        self.run_seed()
        self.client.force_login(self.graders()[1])
        html = self.client.get("/contacts/").content.decode()
        first = html.index('class="contact-name"')
        self.assertIn(">Maya Okafor</a>", html[first:first + 120])
