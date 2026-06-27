import hashlib
import hmac
import json
import time
from unittest.mock import MagicMock

from django.conf import settings
from django.test import TestCase, override_settings

from fastaar import FastaarClient, FastaarException
from fastaar_django import get_fastaar_client, webhook_received, payment_completed


class FastaarDjangoTests(TestCase):
    def setUp(self) -> None:
        self.secret = getattr(settings, "FASTAAR_WEBHOOK_SECRET")
        self.body_dict = {
            "event": "payment.completed",
            "data": {
                "id": "pay_01jxyz",
                "invoice_number": "ORDER-42",
                "amount": 1250,
            },
        }
        self.raw_body = json.dumps(self.body_dict)
        self.timestamp = int(time.time())

    def _generate_signature_header(self, secret: str, timestamp: int, body: str) -> str:
        payload = f"{timestamp}.{body}".encode("utf-8")
        h = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256)
        return f"t={timestamp},v1={h.hexdigest()}"

    def test_get_fastaar_client_configured(self) -> None:
        client = get_fastaar_client()
        self.assertIsInstance(client, FastaarClient)
        self.assertEqual(client.api_key, settings.FASTAAR_API_KEY)
        self.assertEqual(client.timeout_seconds, settings.FASTAAR_TIMEOUT)

    @override_settings(FASTAAR_API_KEY=None)
    def test_get_fastaar_client_missing_key(self) -> None:
        # Should raise configuration_error FastaarException
        with self.assertRaises(FastaarException) as context:
            get_fastaar_client()
        self.assertEqual(context.exception.error_type, "configuration_error")

    def test_webhook_success_triggers_signals(self) -> None:
        sig = self._generate_signature_header(self.secret, self.timestamp, self.raw_body)

        # Track signal calls
        received_events = []
        completed_payments = []

        def on_webhook_received(sender, event_name, data, **kwargs):
            received_events.append((event_name, data))

        def on_payment_completed(sender, invoice_number, payment_id, data, **kwargs):
            completed_payments.append((invoice_number, payment_id, data))

        webhook_received.connect(on_webhook_received)
        payment_completed.connect(on_payment_completed)

        try:
            response = self.client.post(
                "/webhook/",
                data=self.raw_body,
                content_type="application/json",
                HTTP_X_FASTAAR_SIGNATURE=sig,
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, b"OK")

            # Check signals
            self.assertEqual(len(received_events), 1)
            self.assertEqual(received_events[0][0], "payment.completed")
            self.assertEqual(received_events[0][1]["id"], "pay_01jxyz")

            self.assertEqual(len(completed_payments), 1)
            self.assertEqual(completed_payments[0][0], "ORDER-42")
            self.assertEqual(completed_payments[0][1], "pay_01jxyz")
            self.assertEqual(completed_payments[0][2]["amount"], 1250)

        finally:
            webhook_received.disconnect(on_webhook_received)
            payment_completed.disconnect(on_payment_completed)

    def test_webhook_invalid_signature(self) -> None:
        sig = "t=123,v1=badsignature"
        response = self.client.post(
            "/webhook/",
            data=self.raw_body,
            content_type="application/json",
            HTTP_X_FASTAAR_SIGNATURE=sig,
        )

        self.assertEqual(response.status_code, 400)
        decoded_resp = response.json()
        self.assertEqual(decoded_resp["error"], "Invalid signature")

    def test_webhook_invalid_json(self) -> None:
        sig = self._generate_signature_header(self.secret, self.timestamp, "{invalid-json")
        response = self.client.post(
            "/webhook/",
            data="{invalid-json",
            content_type="application/json",
            HTTP_X_FASTAAR_SIGNATURE=sig,
        )

        self.assertEqual(response.status_code, 400)
        decoded_resp = response.json()
        self.assertEqual(decoded_resp["error"], "Invalid JSON")

    def test_webhook_method_not_allowed(self) -> None:
        # GET request should return 405 Method Not Allowed
        response = self.client.get("/webhook/")
        self.assertEqual(response.status_code, 405)

    @override_settings(FASTAAR_WEBHOOK_SECRET=None)
    def test_webhook_missing_secret(self) -> None:
        sig = self._generate_signature_header("secret", self.timestamp, self.raw_body)
        response = self.client.post(
            "/webhook/",
            data=self.raw_body,
            content_type="application/json",
            HTTP_X_FASTAAR_SIGNATURE=sig,
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn(b"FASTAAR_WEBHOOK_SECRET is not configured", response.content)
