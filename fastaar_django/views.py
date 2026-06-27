import json
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from fastaar import FastaarClient, WebhookSignature, FastaarException
from fastaar_django.signals import webhook_received, payment_completed


def get_fastaar_client() -> FastaarClient:
    """
    Initialize and return a FastaarClient instance using Django settings config.
    """
    api_key = getattr(settings, "FASTAAR_API_KEY", None)
    if not api_key:
        raise FastaarException(
            "FASTAAR_API_KEY is not configured in Django settings.",
            "configuration_error",
        )

    timeout = getattr(settings, "FASTAAR_TIMEOUT", 15)

    return FastaarClient(
        api_key=api_key,
        timeout_seconds=timeout,
    )


@csrf_exempt
@require_POST
def webhook_view(request: HttpResponse) -> HttpResponse:
    """
    Verify incoming webhook requests from Fastaar using the signature header.
    Fires `webhook_received` and `payment_completed` Django signals accordingly.
    """
    secret = getattr(settings, "FASTAAR_WEBHOOK_SECRET", None)
    if not secret:
        return HttpResponse("FASTAAR_WEBHOOK_SECRET is not configured.", status=500)

    signature = request.headers.get("X-Fastaar-Signature", "")
    raw_body = request.body

    # Verify signature
    if not WebhookSignature.verify(secret, raw_body, signature):
        return JsonResponse({"error": "Invalid signature"}, status=400)

    # Parse JSON payload
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    event_name = payload.get("event")
    event_data = payload.get("data", {})

    # Trigger general webhook received signal
    webhook_received.send(sender=None, event_name=event_name, data=event_data)

    # Trigger payment completed signal
    if event_name == "payment.completed":
        payment_completed.send(
            sender=None,
            invoice_number=event_data.get("invoice_number"),
            payment_id=event_data.get("id"),
            data=event_data,
        )

    return HttpResponse("OK", status=200)
