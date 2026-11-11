import re
from unittest.mock import patch

from django.test import Client, TestCase
from django.utils import timezone

from .models import Visit

PAGE = "/020c45f"
STATS = "/020c45f/stats"
NICKNAMES = [
    "brainy-squid",
    "amused-cobra",
    "outstanding-flamingo",
    "cooperative-butterfly",
]
CHOICE = "abtest.views.random.choice"


def make_visit(variant, clicked=False):
    return Visit.objects.create(
        variant=variant,
        clicked_at=timezone.now() if clicked else None,
    )


def button_text(response):
    html = response.content.decode()
    return re.search(r'<button[^>]*id="abtest"[^>]*>(.*?)</button>', html, re.S).group(1).strip()


class PageTests(TestCase):
    def test_page_is_public_with_one_button_and_all_nicknames(self):
        response = self.client.get(PAGE)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertEqual(html.count('id="abtest"'), 1)
        self.assertIn(button_text(response), ("kudos", "thanks"))
        for nickname in NICKNAMES:
            self.assertContains(response, nickname)

    def test_button_is_inside_a_post_form_with_csrf_token(self):
        html = self.client.get(PAGE).content.decode()
        form = re.search(r'<form[^>]*method="post"[^>]*>(.*?)</form>', html, re.S | re.I)
        self.assertIsNotNone(form)
        self.assertIn('id="abtest"', form.group(1))
        self.assertIn("csrfmiddlewaretoken", form.group(1))

    def test_new_visitor_can_get_either_variant(self):
        for variant in ("kudos", "thanks"):
            with patch(CHOICE, return_value=variant):
                response = Client().get(PAGE)
            self.assertEqual(button_text(response), variant)


class VariantAndImpressionTests(TestCase):
    def test_variant_is_sticky_for_the_same_visitor(self):
        with patch(CHOICE, return_value="thanks"):
            first = self.client.get(PAGE)
        with patch(CHOICE, return_value="kudos"):
            second = self.client.get(PAGE)
        self.assertEqual(button_text(first), "thanks")
        self.assertEqual(button_text(second), "thanks")

    def test_reloads_count_one_impression(self):
        for _ in range(3):
            self.client.get(PAGE)
        self.assertEqual(Visit.objects.count(), 1)

    def test_each_new_visitor_counts_one_impression(self):
        Client().get(PAGE)
        Client().get(PAGE)
        self.assertEqual(Visit.objects.count(), 2)

    def test_impression_has_a_timestamp(self):
        self.client.get(PAGE)
        self.assertIsNotNone(Visit.objects.get().impression_at)


class ClickTests(TestCase):
    def test_click_redirects_and_counts_one_click_with_timestamp(self):
        self.client.get(PAGE)
        response = self.client.post(PAGE)
        self.assertRedirects(response, PAGE, fetch_redirect_response=False)
        visit = Visit.objects.get()
        self.assertIsNotNone(visit.clicked_at)

    def test_second_click_is_not_counted(self):
        self.client.get(PAGE)
        self.client.post(PAGE)
        first_click_time = Visit.objects.get().clicked_at
        self.client.post(PAGE)
        self.assertEqual(Visit.objects.filter(clicked_at__isnull=False).count(), 1)
        self.assertEqual(Visit.objects.get().clicked_at, first_click_time)

    def test_redirect_after_click_adds_no_impression_and_keeps_variant(self):
        with patch(CHOICE, return_value="thanks"):
            self.client.get(PAGE)
        response = self.client.post(PAGE, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Visit.objects.count(), 1)
        self.assertEqual(Visit.objects.get().variant, "thanks")
        with patch(CHOICE, return_value="kudos"):
            self.assertEqual(button_text(response), "thanks")

    def test_click_without_a_prior_visit_counts_nothing(self):
        response = self.client.post(PAGE)
        self.assertRedirects(response, PAGE, fetch_redirect_response=False)
        self.assertEqual(Visit.objects.count(), 0)

    def test_csrf_token_is_required(self):
        client = Client(enforce_csrf_checks=True)
        client.get(PAGE)
        self.assertEqual(client.post(PAGE).status_code, 403)
        token = client.cookies["csrftoken"].value
        response = client.post(PAGE, {"csrfmiddlewaretoken": token})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Visit.objects.filter(clicked_at__isnull=False).count(), 1)


class StatsTests(TestCase):
    def fill(self, kudos_imp, kudos_clicks, thanks_imp, thanks_clicks):
        for i in range(kudos_imp):
            make_visit("kudos", clicked=i < kudos_clicks)
        for i in range(thanks_imp):
            make_visit("thanks", clicked=i < thanks_clicks)

    def test_kudos_higher(self):
        self.fill(10, 5, 10, 2)
        data = self.client.get(STATS).json()
        self.assertEqual(data["preferred"], "kudos")
        self.assertEqual(data["kudos"], {"impressions": 10, "clicks": 5})
        self.assertEqual(data["thanks"], {"impressions": 10, "clicks": 2})

    def test_thanks_higher(self):
        self.fill(10, 1, 10, 4)
        self.assertEqual(self.client.get(STATS).json()["preferred"], "thanks")

    def test_rate_is_clicks_over_impressions_not_raw_clicks(self):
        self.fill(100, 10, 10, 5)
        self.assertEqual(self.client.get(STATS).json()["preferred"], "thanks")

    def test_zero_data_returns_valid_json(self):
        response = self.client.get(STATS)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "preferred": "kudos",
                "kudos": {"impressions": 0, "clicks": 0},
                "thanks": {"impressions": 0, "clicks": 0},
            },
        )

    def test_tie_returns_kudos(self):
        self.fill(10, 3, 10, 3)
        self.assertEqual(self.client.get(STATS).json()["preferred"], "kudos")

    def test_one_variant_without_impressions_does_not_crash(self):
        self.fill(0, 0, 4, 1)
        data = self.client.get(STATS).json()
        self.assertEqual(data["preferred"], "thanks")

    def test_stats_is_public_json_and_live(self):
        self.assertEqual(self.client.get(STATS)["Content-Type"], "application/json")
        make_visit("thanks", clicked=True)
        self.assertEqual(self.client.get(STATS).json()["thanks"]["clicks"], 1)
