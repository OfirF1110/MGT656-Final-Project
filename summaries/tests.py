import json
from http.client import IncompleteRead
from unittest.mock import patch
from urllib.error import URLError

from django.contrib.auth import get_user_model
from django.test import TestCase, SimpleTestCase, override_settings, Client
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.urls import reverse

from .services import summarize_notes, SummaryError

def response_bytes(sentences=None):
    return json.dumps({"choices": [{"finish_reason": "stop", "message": {
        "content": json.dumps({"sentences": sentences or ["We discussed the role.", "The team values collaboration."]})
    }}]}).encode()

@override_settings(OPENROUTER_API_KEY="test-key-only", OPENROUTER_MODEL="test-model-only")
class ServiceTests(SimpleTestCase):
    def call_with(self, raw):
        with patch("summaries.services.urlopen") as call:
            call.return_value.__enter__.return_value.read.return_value = raw
            result = summarize_notes("Invented notes")
            return result, call

    def test_success_and_server_request(self):
        summary, call = self.call_with(response_bytes())
        self.assertEqual(summary, "We discussed the role. The team values collaboration.")
        request = call.call_args.args[0]
        self.assertEqual(request.full_url, "https://openrouter.ai/api/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key-only")
        body = json.loads(request.data)
        self.assertEqual(body["model"], "test-model-only")
        self.assertEqual(body["max_tokens"], 1000)
        self.assertEqual(body["messages"][-1]["content"], "Invented notes")
        self.assertEqual(call.call_args.kwargs["timeout"], 20)

    def test_three_sentences(self):
        summary, _ = self.call_with(response_bytes(["First fact.", "Second fact.", "Third fact."]))
        self.assertEqual(summary, "First fact. Second fact. Third fact.")

    def test_protocol_fragments_are_rejected_without_logging_content(self):
        fragments = [
            'The budget is undecided. assistant{ sentences : ["Extra text."]}',
            'The budget is undecided. {"sentences": ["Extra text."]}',
            "The budget is undecided. <|im_start|>assistant",
            "The budget is undecided. [INST]continue[/INST]",
            "The budget is undecided. #conversation_id private-id",
            "The budget is undecided. #message_id private-id",
            "The budget is undecided.\x81",
            "The budget is undecided. ```json",
        ]
        for fragment in fragments:
            with self.subTest(fragment=repr(fragment)), self.assertLogs("summaries.services", "WARNING") as logs:
                with self.assertRaises(SummaryError):
                    self.call_with(response_bytes(["We discussed the workshop.", fragment]))
            self.assertEqual(logs.output, [
                "WARNING:summaries.services:AI summary failed: category=sentence_protocol_fragment"])

    def test_normal_roles_quotes_and_multilingual_text_are_preserved(self):
        sentences = [
            'The assistant discussed user research with Dr. Lee and quoted "keep it simple".',
            "团队将在周五确认预算，预计为 $1,000.50。",
        ]
        summary, _ = self.call_with(response_bytes(sentences))
        self.assertEqual(summary, " ".join(sentences))

    def test_request_enforces_structured_summary_contract(self):
        _, call = self.call_with(response_bytes())
        body = json.loads(call.call_args.args[0].data)
        self.assertEqual(body["provider"], {"require_parameters": True})
        output = body["response_format"]
        self.assertEqual(output["type"], "json_schema")
        self.assertTrue(output["json_schema"]["strict"])
        schema = output["json_schema"]["schema"]
        self.assertEqual(schema["required"], ["sentences"])
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["sentences"]["minItems"], 2)
        self.assertEqual(schema["properties"]["sentences"]["maxItems"], 3)
        self.assertEqual(schema["properties"]["sentences"]["items"],
                         {"type": "string", "minLength": 1, "maxLength": 1000})
        call.assert_called_once()

    def test_one_item_response_is_still_rejected_without_retry(self):
        with patch("summaries.services.urlopen") as call:
            call.return_value.__enter__.return_value.read.return_value = response_bytes(
                ["First sentence. Second sentence."])
            with self.assertRaises(SummaryError):
                summarize_notes("Invented notes")
            call.assert_called_once()

    def test_fenced_json_summary(self):
        for fence in ("```json", "```", "```JSON"):
            with self.subTest(fence=fence):
                data = json.loads(response_bytes())
                content = data["choices"][0]["message"]["content"]
                data["choices"][0]["message"]["content"] = f"  \n{fence}\n{content}\n```\n "
                summary, _ = self.call_with(json.dumps(data).encode())
                self.assertEqual(summary, "We discussed the role. The team values collaboration.")

    def test_fences_do_not_bypass_validation(self):
        valid = json.dumps({"sentences": ["First fact.", "Second fact."]})
        for content in (f"```json\n{valid}", f"Explanation\n```json\n{valid}\n```",
                        "```json\nnot json\n```", '```json\n{"sentences": ["Only one."]}\n```'):
            with self.subTest(content=content), self.assertRaises(SummaryError):
                data = json.loads(response_bytes())
                data["choices"][0]["message"]["content"] = content
                self.call_with(json.dumps(data).encode())

    def test_malformed_outputs(self):
        invalid = [b"not json", b"null", b"[]", b"{}", b'{"choices":[]}',
                   b'{"error":{"message":"secret upstream message"}}',
                   response_bytes(["Only one."]), response_bytes(["A.", "", "B."]),
                   response_bytes(["A.", 12]), b"x" * 65537]
        for raw in invalid:
            with self.subTest(raw=raw[:60]), self.assertRaises(SummaryError):
                self.call_with(raw)

    def test_truncated_and_non_text_outputs(self):
        for choice in [{"finish_reason": "length", "message": {"content": "{}"}},
                       {"finish_reason": "stop", "message": {"content": None}}]:
            with self.subTest(choice=choice), self.assertRaises(SummaryError):
                self.call_with(json.dumps({"choices": [choice]}).encode())

    def test_network_errors_are_sanitized(self):
        for error in [URLError("secret-key"), TimeoutError("private notes")]:
            with patch("summaries.services.urlopen", side_effect=error):
                with self.assertRaises(SummaryError) as caught:
                    summarize_notes("notes")
                self.assertNotIn("secret-key", str(caught.exception))
                self.assertNotIn("private notes", str(caught.exception))

    def test_missing_configuration_never_calls_provider(self):
        for config in [{"OPENROUTER_API_KEY": ""}, {"OPENROUTER_MODEL": ""}]:
            with self.settings(**config), patch("summaries.services.urlopen") as call:
                with self.assertRaises(SummaryError):
                    summarize_notes("notes")
                call.assert_not_called()

    def test_diagnostics_log_only_safe_categories(self):
        cases = [
            (b"private response", "envelope_json"),
            (b'{}', "envelope_shape"),
            (b'{"error":{"message":"private provider detail"}}', "provider_error"),
            (b"x" * 65537, "response_too_large"),
            (response_bytes(["Only one private sentence."]), "sentence_count_1"),
        ]
        for content, category in [("private output", "summary_json"),
                                  ('{"private-key": "private value"}', "summary_shape"),
                                  (None, "content_shape")]:
            data = json.loads(response_bytes())
            data["choices"][0]["message"]["content"] = content
            cases.append((json.dumps(data).encode(), category))
        for reason, category in [("length", "finish_length"),
                                 ("private provider reason", "finish_other")]:
            data = json.loads(response_bytes())
            data["choices"][0]["finish_reason"] = reason
            cases.append((json.dumps(data).encode(), category))
        for raw, category in cases:
            with self.subTest(category=category), self.assertLogs("summaries.services", "WARNING") as logs:
                with self.assertRaises(SummaryError):
                    self.call_with(raw)
            self.assertEqual(logs.output, [
                f"WARNING:summaries.services:AI summary failed: category={category}"])
            self.assertIsNone(logs.records[0].exc_info)

    def test_transport_logs_never_include_exception_or_notes(self):
        with patch("summaries.services.urlopen", side_effect=URLError("private secret")):
            with self.assertLogs("summaries.services", "WARNING") as logs:
                with self.assertRaises(SummaryError):
                    summarize_notes("private notes")
        self.assertEqual(logs.output, [
            "WARNING:summaries.services:AI summary failed: category=transport"])
        self.assertIsNone(logs.records[0].exc_info)

    def test_sentence_diagnostics_distinguish_each_constraint(self):
        cases = [
            ("private text", "sentences_not_list"),
            (None, "sentences_not_list"),
            ([], "sentence_count_0"),
            (["A."] * 4, "sentence_count_4"),
            (["A.", {"private": "value"}], "sentence_not_text"),
            (["A.", " \n\t"], "sentence_empty"),
            (["A.", "x" * 1001], "sentence_too_long"),
        ]
        for sentences, category in cases:
            data = json.loads(response_bytes())
            data["choices"][0]["message"]["content"] = json.dumps({"sentences": sentences})
            with self.subTest(category=category), self.assertLogs("summaries.services", "WARNING") as logs:
                with self.assertRaises(SummaryError):
                    self.call_with(json.dumps(data).encode())
            self.assertEqual(logs.output, [
                f"WARNING:summaries.services:AI summary failed: category={category}"])
            self.assertIsNone(logs.records[0].exc_info)

@override_settings(SECURE_SSL_REDIRECT=False)
class SummaryPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user("summary-tester", password="test-only-password")

    def setUp(self):
        self.url = reverse("summaries:create")
        self.client.force_login(self.user)

    def test_login_required_get_and_post(self):
        self.client.logout()
        with patch("summaries.services.urlopen") as call:
            for method in [self.client.get, self.client.post]:
                self.assertEqual(method(self.url).status_code, 302)
            call.assert_not_called()

    def test_page_and_navigation(self):
        response = self.client.get(self.url)
        self.assertContains(response, "Summarize with AI")
        self.assertContains(response, 'name="notes"')
        self.assertIn("no-store", response["Cache-Control"])

    def test_empty_and_whitespace_make_no_call(self):
        with patch("summaries.views.summarize_notes") as call:
            for notes in ["", " \n\t "]:
                response = self.client.post(self.url, {"notes": notes})
                self.assertContains(response, "Paste some notes first")
                self.assertContains(response, "is-invalid")
                self.assertContains(response, 'aria-invalid="true"')
                self.assertContains(response, 'id="id_notes-error"')
            call.assert_not_called()

    def test_long_notes_make_no_call(self):
        with patch("summaries.views.summarize_notes") as call:
            response = self.client.post(self.url, {"notes": "a" * 12001})
            self.assertTrue(response.context["form"].errors)
            call.assert_not_called()

    @override_settings(OPENROUTER_API_KEY="test-secret-key", OPENROUTER_MODEL="test-model-only")
    def test_success_no_database_writes_or_secrets(self):
        with patch("summaries.services.urlopen") as call:
            call.return_value.__enter__.return_value.read.return_value = response_bytes()
            with CaptureQueriesContext(connection) as queries:
                response = self.client.post(self.url, {"notes": "Invented meeting notes"})
        self.assertContains(response, "We discussed the role.")
        self.assertContains(response, "Invented meeting notes")
        html = response.content.decode()
        self.assertLess(html.index('id="summary-title"'), html.index('name="notes"'))
        self.assertContains(response, 'maxlength="12000"')
        self.assertNotContains(response, "test-secret-key")
        self.assertNotContains(response, "test-model-only")
        self.assertFalse(any(q["sql"].lstrip().upper().startswith(
            ("INSERT", "UPDATE", "DELETE")) for q in queries))

    @override_settings(OPENROUTER_API_KEY="test-secret-key", OPENROUTER_MODEL="test-model-only")
    def test_failure_and_malformed_keep_original_notes(self):
        notes = "  Original notes\n<script>alert(1)</script>  "
        for raw, error in [(None, URLError("upstream secret")), (b"{}", None)]:
            with patch("summaries.services.urlopen") as call:
                if error:
                    call.side_effect = error
                else:
                    call.return_value.__enter__.return_value.read.return_value = raw
                response = self.client.post(self.url, {"notes": notes})
            self.assertEqual(response.context["form"]["notes"].value(), notes)
            self.assertContains(response, "Your notes are still here")
            self.assertNotContains(response, "<script>alert(1)</script>")
            self.assertNotContains(response, "upstream secret")

    def test_output_is_escaped(self):
        with patch("summaries.views.summarize_notes", return_value="<script>alert(1)</script>"):
            response = self.client.post(self.url, {"notes": "notes"})
        self.assertNotContains(response, "<script>alert(1)</script>")
        self.assertContains(response, "&lt;script&gt;")

    @override_settings(OPENROUTER_API_KEY="test-secret-key", OPENROUTER_MODEL="test-model-only")
    def test_protocol_fragment_shows_error_and_preserves_notes(self):
        notes = "Fictional workshop notes."
        with patch("summaries.services.urlopen") as call:
            call.return_value.__enter__.return_value.read.return_value = response_bytes(
                ["We discussed the workshop.", 'assistant{ sentences: ["private fragment"]}'])
            response = self.client.post(self.url, {"notes": notes})
        self.assertContains(response, "Your notes are still here")
        self.assertEqual(response.context["form"]["notes"].value(), notes)
        self.assertNotContains(response, "private fragment")
        self.assertNotContains(response, 'id="summary-title"')
        call.assert_called_once()

    @override_settings(OPENROUTER_API_KEY="test-secret-key", OPENROUTER_MODEL="test-model-only")
    def test_interrupted_response_keeps_notes_without_500(self):
        notes = "  Original notes\n<script>alert(1)</script>  "
        with patch("summaries.services.urlopen") as call:
            call.return_value.__enter__.return_value.read.side_effect = IncompleteRead(
                b"private upstream response", 100)
            response = self.client.post(self.url, {"notes": notes})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"]["notes"].value(), notes)
        self.assertContains(response, "Your notes are still here")
        self.assertNotContains(response, "private upstream response")
        self.assertNotContains(response, "test-secret-key")
        self.assertNotContains(response, "<script>alert(1)</script>")

    def test_csrf_is_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        with patch("summaries.views.summarize_notes") as call:
            self.assertEqual(client.post(self.url, {"notes": "notes"}).status_code, 403)
            call.assert_not_called()
