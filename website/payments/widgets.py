"""Widgets provided by the payments package"""

from django.forms import Widget

from payments.models import Payment


class PaymentWidget(Widget):
    """
    Custom widget for the Payment object, used in registrations
    """

    template_name = "payments/widgets/payment.html"

    def get_context(self, name, value, attrs) -> dict:
        # TODO @sebas
        context = super().get_context(name, value, attrs)
        if value:
            payment = Payment.objects.get(pk=value)
            context["url"] = payment.get_admin_url()
            context["payment"] = payment
        return context

    class Media:
        js = ("admin/payments/js/payments.js",)


class SignatureWidget(Widget):
    """
    Widget for signature image
    """

    template_name = "payments/widgets/signature.html"

    class Media:
        js = (
            "payments/js/signature_pad.min.js",
            "payments/js/main.js",
        )
        css = {"all": ("admin/payments/css/signature.css",)}
