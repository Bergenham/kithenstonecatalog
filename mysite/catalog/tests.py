from django.template.loader import get_template
from django.test import RequestFactory, SimpleTestCase

from .views import _save_user_bid_response


class QuartzCatalogTemplateTests(SimpleTestCase):
    def test_ajax_fragment_template_is_loadable(self):
        template = get_template("fronttemp/quartz/_stones_grid_Q.html")

        self.assertIsNotNone(template)


class StoneBidValidationTests(SimpleTestCase):
    def test_invalid_bid_returns_field_errors_without_saving(self):
        request = RequestFactory().post(
            "/catalog/quartz/stone/test",
            data={
                "full_name": "Иван",
                "phone": "invalid",
                "email": "invalid",
            },
        )

        response = _save_user_bid_response(request)

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content,
            {
                "status": "error",
                "message": "Проверьте заполнение формы.",
                "errors": {
                    "phone": [{"message": "Введите номер в российском формате.", "code": ""}],
                    "email": [{"message": "Enter a valid email address.", "code": "invalid"}],
                    "privacyPolicy": [{"message": "This field is required.", "code": "required"}],
                },
            },
        )
