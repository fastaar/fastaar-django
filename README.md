# Fastaar Django Plugin

Integrate bKash & Nagad payments seamlessly into your Django website/application via Fastaar.

This Django app wraps the `fastaar-python` SDK, exposes standard webhook views (CSRF-exempt and signature-verified), and dispatches Django signals when payments are completed.

## Install

Install the package via `pip` (along with `fastaar-python`):

```bash
pip install fastaar-django
```

## Configuration

1. Add `fastaar_django` to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'fastaar_django',
]
```

2. Add your Fastaar credentials in `settings.py`:

```python
FASTAAR_API_KEY = 'fk_live_...'       # fk_live_... or fk_test_...
FASTAAR_WEBHOOK_SECRET = 'whsec_...'  # Your merchant webhook secret
FASTAAR_TIMEOUT = 15                  # Optional (defaults to 15)
```

## Setup Webhook Route

In your main `urls.py`, register the Fastaar webhook URL:

```python
from django.urls import path, include

urlpatterns = [
    # ...
    path('fastaar/', include('fastaar_django.urls')),
]
```

This will expose the endpoint `/fastaar/webhook/` (e.g. `https://your-domain.com/fastaar/webhook/`) which you should register in your Fastaar dashboard.

## Handle Webhooks (Django Signals)

The plugin automatically verifies incoming webhook signatures and raises custom signals. You can listen to these signals in your Django apps:

```python
from django.dispatch import receiver
from fastaar_django.signals import payment_completed, webhook_received

@receiver(payment_completed)
def handle_payment_completed(sender, invoice_number, payment_id, data, **kwargs):
    # invoice_number matches your internal ORDER-42 identifier
    # payment_id matches the Fastaar payment ID (e.g., 01jxyz...)
    
    # Mark the order as paid in your database, idempotently
    print(f"Order {invoice_number} successfully paid. Fastaar payment ID: {payment_id}")

@receiver(webhook_received)
def handle_any_webhook(sender, event_name, data, **kwargs):
    # Triggered on any incoming validated Fastaar webhook event
    print(f"Received Fastaar event: {event_name}")
```

> [!IMPORTANT]
> To ensure your signal receivers are loaded, make sure to import them in your Django app's `AppConfig.ready()` method.

## Making API Calls

The plugin provides a helper function to get an initialized `FastaarClient` preloaded with settings from your Django configuration:

```python
from fastaar_django import get_fastaar_client

fastaar = get_fastaar_client()

# Create a payment intent
payment = fastaar.create_payment({
    'amount': 1250,
    'invoice_number': 'ORDER-42',               # required — your order reference
    'success_url': 'https://shop.example.com/thanks',
    'cancel_url': 'https://shop.example.com/cart',
})

# Redirect user to checkout url
checkout_url = payment['checkout_url']
```

## Customers

The underlying `FastaarClient` exposes the full Customers API:

```python
from fastaar_django import get_fastaar_client

fastaar = get_fastaar_client()

# Create a customer — name and phone are required
customer = fastaar.create_customer({
    'name':  'Rahim Uddin',
    'phone': '01712345678',
    'email': 'rahim@example.com',   # optional
})

# Retrieve, update, list
customer  = fastaar.get_customer(customer['id'])
customer  = fastaar.update_customer(customer['id'], {'name': 'Rahim Ahmed'})
customers = fastaar.list_customers({'email': 'rahim@example.com'})
```
