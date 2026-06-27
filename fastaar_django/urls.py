from django.urls import path

from fastaar_django.views import webhook_view

app_name = "fastaar_django"

urlpatterns = [
    path("webhook/", webhook_view, name="webhook"),
]
