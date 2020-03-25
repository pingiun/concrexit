"""Admin views provided by the payments package"""
from django.contrib import messages
from django.contrib.admin.utils import model_ngettext
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator
from django.views import View

from payments import services
from .models import Payment


@method_decorator(staff_member_required, name="dispatch")
@method_decorator(
    permission_required("payments.process_payments"), name="dispatch",
)
class PaymentAdminView(View):
    """
    View that processes a payment
    """

    def post(self, request, *args, **kwargs):
        payable = None # Payment.objects.filter(pk=kwargs["pk"]) # TODO fix

        if not ("type" in request.POST):
            return redirect("admin:payments_payment_change", kwargs["pk"])

        result = services.create_payment(payable, request.member, request.POST["type"])

        if result:
            messages.success(
                request, _("Successfully paid %s.") % model_ngettext(payable.payment_topic, 1)
            )
        else:
            messages.error(
                request, _("Could not pay %s.") % model_ngettext(payable.payment_topic, 1)
            )

        if "next" in request.POST:
            return redirect(request.POST["next"])

        return redirect("admin:payments_payment_change", kwargs["pk"])
