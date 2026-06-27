from django.dispatch import Signal

# Triggered when any valid Fastaar webhook event is received
# Sent with kwargs: event_name, data
webhook_received = Signal()

# Triggered when a validated payment.completed event is received
# Sent with kwargs: invoice_number, payment_id, data
payment_completed = Signal()

# Triggered when a validated payment.refunded event is received
# Sent with kwargs: invoice_number, payment_id, data
payment_refunded = Signal()
