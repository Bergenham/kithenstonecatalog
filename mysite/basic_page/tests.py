import json
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase
from openpyxl import load_workbook
from PIL import Image

from .forms import UserBidForm
from .utils.table_export import display_export_value, export_stones, safe_spreadsheet_value
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

    def test_missing_values_have_a_readable_export_value(self):
        self.assertEqual(display_export_value(None), 'Отсутствует')
        self.assertEqual(display_export_value('None'), 'Отсутствует')
        self.assertEqual(display_export_value(''), 'Отсутствует')

    def test_export_with_images_embeds_preview_and_example_images(self):
        def image_file(name):
            image_bytes = BytesIO()
            Image.new('RGB', (10, 10), 'white').save(image_bytes, format='PNG')

            class TestImage(BytesIO):
                def __init__(self):
                    super().__init__(image_bytes.getvalue())
                    self.name = name

                def open(self, mode):
                    self.seek(0)

            return TestImage()

        preview = image_file('preview.png')
        example = image_file('example.png')
        stone = SimpleNamespace(
            pk=1, name_stone='Stone name', abt_prise=None, material=None,
            country=None, thickness=None, article=None, about_brand=None,
            archive=False, priview_img=preview,
            example_images=SimpleNamespace(all=lambda: [SimpleNamespace(image=example)]),
            get_material_display=lambda: None,
            get_country_display=lambda: None,
            get_brand_stone_display=lambda: None,
            get_color_display=lambda: None,
            get_texture_display=lambda: None,
            get_faktura_display=lambda: None,
            get_link_serf_display=lambda: 'Readable certificate',
        )
        model = SimpleNamespace(
            objects=SimpleNamespace(
                prefetch_related=lambda *args: SimpleNamespace(all=lambda: [stone]),
            ),
        )

        response = export_stones(
            RequestFactory().get('/export?with_images=1'), model, 'stones', 'Stones',
        )
        worksheet = load_workbook(BytesIO(response.content)).active

        self.assertEqual(worksheet['N1'].value, 'Превью')
        self.assertEqual(worksheet['O1'].value, 'Пример изображения №1')
        self.assertEqual(worksheet['B2'].value, 'Отсутствует')
        self.assertEqual(worksheet['M2'].value, 'Readable certificate')
        self.assertEqual(len(worksheet._images), 2)
