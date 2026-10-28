import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase

from .forms import UserBidForm
from .utils.table_export import safe_spreadsheet_value
from .views import choice_stone, contacts, export_userbids_view


class UserBidFormTests(SimpleTestCase):
    valid_data = {
        "full_name": "Иван Петров",
        "phone": "+7 (999) 123-45-67",
        "email": "ivan@example.com",
        "privacyPolicy": "on",
    }

    def test_valid_form_sets_confirmed_privacy_consent(self):
        form = UserBidForm(data=self.valid_data)

        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.save(commit=False).AWtPP)

    def test_form_rejects_missing_privacy_consent(self):
        data = self.valid_data.copy()
        data.pop("privacyPolicy")

        form = UserBidForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("privacyPolicy", form.errors)

    def test_form_rejects_invalid_phone(self):
        data = self.valid_data | {"phone": "not-a-phone"}

        form = UserBidForm(data=data)

        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)


class ExportUserBidsViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_export_requires_staff_user(self):
        request = self.factory.get("/X5KD08OHn25yNLf")
        request.user = AnonymousUser()

        response = export_userbids_view(request)

        self.assertEqual(response.status_code, 302)

    @patch("basic_page.views.export_userbids")
    def test_staff_export_passes_request_to_workbook_builder(self, export_userbids):
        workbook = Mock()
        export_userbids.return_value = workbook
        request = self.factory.get("/X5KD08OHn25yNLf")
        request.user = SimpleNamespace(is_active=True, is_staff=True)

        response = export_userbids_view(request)

        self.assertEqual(response.status_code, 200)
        export_userbids.assert_called_once_with(request)
        workbook.save.assert_called_once_with(response)


class ContactsValidationTests(SimpleTestCase):
    def test_ajax_contact_form_returns_validation_errors(self):
        request = RequestFactory().post(
            "/calculator",
            data={
                "full_name": "Иван",
                "phone": "invalid",
                "email": "invalid",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        response = contacts(request)

        self.assertEqual(response.status_code, 400)
        payload = json.loads(response.content)
        self.assertEqual(payload["status"], "error")
        self.assertIn("privacyPolicy", payload["errors"])

    def test_ajax_choice_form_returns_validation_errors(self):
        request = RequestFactory().post(
            "/choice",
            data={
                "full_name": "Иван",
                "phone": "invalid",
                "email": "invalid",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        response = choice_stone(request)

        self.assertEqual(response.status_code, 400)
        payload = json.loads(response.content)
        self.assertEqual(payload["status"], "error")
        self.assertIn("privacyPolicy", payload["errors"])


class SpreadsheetExportTests(SimpleTestCase):
    def test_formula_like_value_is_exported_as_plain_text(self):
        self.assertEqual(safe_spreadsheet_value("=HYPERLINK(\"https://example.com\")"), "'=HYPERLINK(\"https://example.com\")")
        self.assertEqual(safe_spreadsheet_value("ordinary text"), "ordinary text")
