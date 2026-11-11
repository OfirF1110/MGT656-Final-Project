import os
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

CREDS = {
    "GRADER_ADMIN_USERNAME": "grader-admin@example.com",
    "GRADER_ADMIN_PASSWORD": "Example-Only-Admin-752!",
    "GRADER_MEMBER_USERNAME": "grader-member@example.com",
    "GRADER_MEMBER_PASSWORD": "Example-Only-Member-981!",
}

class FoundationTests(TestCase):
    def test_public_pages_and_protected_account(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/health/").json(), {"status": "ok"})
        self.assertRedirects(self.client.get("/account/"), "/login/?next=/account/")

    @patch.dict(os.environ, CREDS)
    def test_seed_twice_and_login_logout(self):
        call_command("seed", verbosity=0)
        ids = list(get_user_model().objects.values_list("id", flat=True))
        call_command("seed", verbosity=0)
        self.assertEqual(list(get_user_model().objects.values_list("id", flat=True)), ids)
        for role in ("ADMIN", "MEMBER"):
            user = get_user_model().objects.get(username=CREDS[f"GRADER_{role}_USERNAME"])
            self.assertEqual(user.is_superuser, role == "ADMIN")
            self.assertNotEqual(user.password, CREDS[f"GRADER_{role}_PASSWORD"])
            response = self.client.post("/login/", {"username": user.username, "password": CREDS[f"GRADER_{role}_PASSWORD"]})
            self.assertRedirects(response, "/account/")
            self.assertContains(self.client.get("/account/"), user.username)
            self.assertEqual(self.client.get("/logout/").status_code, 405)
            self.assertRedirects(self.client.post("/logout/"), "/login/")
            self.assertEqual(self.client.get("/account/").status_code, 302)

    @patch.dict(os.environ, CREDS)
    def test_invalid_login_and_external_redirect(self):
        call_command("seed", verbosity=0)
        self.assertContains(self.client.post("/login/", {"username": CREDS["GRADER_MEMBER_USERNAME"], "password": "wrong"}), "Please enter a correct")
        response = self.client.post("/login/", {"username": CREDS["GRADER_MEMBER_USERNAME"], "password": CREDS["GRADER_MEMBER_PASSWORD"], "next": "https://example.com/"})
        self.assertRedirects(response, "/account/")

    @patch.dict(os.environ, {**CREDS, "GRADER_MEMBER_PASSWORD": ""})
    def test_missing_secret_creates_no_accounts(self):
        with self.assertRaises(CommandError):
            call_command("seed")
        self.assertEqual(get_user_model().objects.count(), 0)

    @patch.dict(os.environ, CREDS)
    def test_seed_refuses_existing_password_collision_atomically(self):
        user = get_user_model().objects.create_user(CREDS["GRADER_MEMBER_USERNAME"], password="Existing-Different-Secret-321")
        with self.assertRaises(CommandError):
            call_command("seed")
        self.assertEqual(get_user_model().objects.count(), 1)
        user.refresh_from_db()
        self.assertTrue(user.check_password("Existing-Different-Secret-321"))
