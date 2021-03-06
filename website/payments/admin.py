"""Registers admin interfaces for the payments module"""
import csv
from collections import OrderedDict

from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.contrib.admin.utils import model_ngettext
from django.db.models import QuerySet
from django.db.models.query_utils import Q
from django.http import HttpResponse, HttpRequest
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from members.models import Member
from payments import services, admin_views
from payments.forms import BankAccountAdminForm
from .models import Payment, BankAccount


def _show_message(
    admin: ModelAdmin, request: HttpRequest, n: int, message: str, error: str
) -> None:
    if n == 0:
        admin.message_user(request, error, messages.ERROR)
    else:
        admin.message_user(
            request,
            message % {"count": n, "items": model_ngettext(admin.opts, n)},
            messages.SUCCESS,
        )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Manage the payments"""

    list_display = (
        "created_at",
        "amount",
        "processing_date",
        "type",
        "paid_by_link",
        "processed_by_link",
        "topic",
    )
    list_filter = ("type",)
    list_select_related = (
        "paid_by",
        "processed_by",
    )
    date_hierarchy = "created_at"
    fields = (
        "created_at",
        "amount",
        "type",
        "processing_date",
        "paid_by",
        "processed_by",
        "topic",
        "notes",
    )
    readonly_fields = (
        "created_at",
        "amount",
        "type",
        "processing_date",
        "paid_by",
        "processed_by",
        "topic",
        "notes",
    )
    search_fields = (
        "topic",
        "notes",
        "paid_by__username",
        "paid_by__first_name",
        "paid_by__last_name",
        "processed_by__username",
        "processed_by__first_name",
        "processed_by__last_name",
        "amount",
    )
    ordering = ("-created_at", "processing_date")
    autocomplete_fields = ("paid_by", "processed_by")
    actions = [
        "process_cash_selected",
        "process_card_selected",
        "process_tpay_selected",
        "process_wire_selected",
        "export_csv",
    ]

    @staticmethod
    def _member_link(member: Member) -> str:
        if member:
            return format_html(
                "<a href='{}'>{}</a>", member.get_absolute_url(), member.get_full_name()
            )
        else:
            return "-"

    def paid_by_link(self, obj: Payment) -> str:
        return self._member_link(obj.paid_by)

    paid_by_link.admin_order_field = "paid_by"
    paid_by_link.short_description = _("paid by")

    def processed_by_link(self, obj: Payment) -> str:
        return self._member_link(obj.processed_by)

    processed_by_link.admin_order_field = "processed_by"
    processed_by_link.short_description = _("processed by")

    def changeform_view(
        self,
        request: HttpRequest,
        object_id: int = None,
        form_url: str = "",
        extra_context: dict = None,
    ) -> HttpResponse:
        """
        Renders the change formview
        Only allow when the payment has not been processed yet
        """
        obj = None
        if object_id is not None and request.user.has_perm("payments.process_payments"):
            obj = Payment.objects.get(id=object_id)
            if obj.processed:
                obj = None
        return super().changeform_view(request, object_id, form_url, {"payment": obj})

    def get_readonly_fields(self, request: HttpRequest, obj: Payment = None):
        if not obj:
            return "created_at", "type", "processing_date", "processed_by"
        return super().get_readonly_fields(request, obj)

    def get_actions(self, request: HttpRequest) -> OrderedDict:
        """Get the actions for the payments"""
        """Hide the processing actions if the right permissions are missing"""
        actions = super().get_actions(request)
        if not request.user.has_perm("payments.process_payments"):
            del actions["process_cash_selected"]
            del actions["process_card_selected"]
            del actions["process_tpay_selected"]
            del actions["process_wire_selected"]
        return actions

    def process_cash_selected(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Process the selected payment as cash"""
        if request.user.has_perm("payments.process_payments"):
            updated_payments = services.process_payment(
                queryset, request.member, Payment.CASH
            )
            self._process_feedback(request, updated_payments)

    process_cash_selected.short_description = _("Process selected payments (cash)")

    def process_card_selected(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Process the selected payment as card"""
        if request.user.has_perm("payments.process_payments"):
            updated_payments = services.process_payment(
                queryset, request.member, Payment.CARD
            )
            self._process_feedback(request, updated_payments)

    process_card_selected.short_description = _("Process selected payments (card)")

    def process_tpay_selected(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Process the selected payment as Thalia Pay"""
        if request.user.has_perm("payments.process_payments"):
            updated_payments = services.process_payment(
                queryset, request.member, Payment.TPAY
            )
            self._process_feedback(request, updated_payments)

    process_tpay_selected.short_description = _(
        "Process selected payments (Thalia Pay, only if enabled)"
    )

    def process_wire_selected(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Process the selected payment as wire"""
        if request.user.has_perm("payments.process_payments"):
            updated_payments = services.process_payment(
                queryset, request.member, Payment.WIRE
            )
            self._process_feedback(request, updated_payments)

    process_wire_selected.short_description = _("Process selected payments (wire)")

    def _process_feedback(self, request, updated_payments: list) -> None:
        """Show a feedback message for the processing result"""
        rows_updated = len(updated_payments)
        _show_message(
            self,
            request,
            rows_updated,
            message=_("Successfully processed %(count)d %(items)s."),
            error=_("The selected payment(s) could not be processed."),
        )

    def get_urls(self) -> list:
        urls = super().get_urls()
        custom_urls = [
            path(
                "<uuid:pk>/process/",
                self.admin_site.admin_view(admin_views.PaymentAdminView.as_view()),
                name="payments_payment_process",
            ),
        ]
        return custom_urls + urls

    def export_csv(self, request: HttpRequest, queryset: QuerySet) -> HttpResponse:
        """
        Export a CSV of payments
        :param request: Request
        :param queryset: Items to be exported
        """
        response = HttpResponse(content_type="text/csv")
        response[
            "Content-Disposition"
        ] = 'attachment;\
                                           filename="payments.csv"'
        writer = csv.writer(response)
        headers = [
            _("created"),
            _("processed"),
            _("amount"),
            _("type"),
            _("processor"),
            _("payer id"),
            _("payer name"),
            _("notes"),
        ]
        writer.writerow([capfirst(x) for x in headers])
        for payment in queryset:
            writer.writerow(
                [
                    payment.created_at,
                    payment.processing_date,
                    payment.amount,
                    payment.get_type_display(),
                    payment.processed_by.get_full_name()
                    if payment.processed_by
                    else "-",
                    payment.paid_by.pk if payment.paid_by else "-",
                    payment.paid_by.get_full_name() if payment.paid_by else "-",
                    payment.notes,
                ]
            )
        return response

    export_csv.short_description = _("Export")


class ValidAccountFilter(admin.SimpleListFilter):
    """Filter the memberships by whether they are active or not"""

    title = _("mandates")
    parameter_name = "active"

    def lookups(self, request, model_name) -> tuple:
        return (
            ("valid", _("Valid")),
            ("invalid", _("Invalid")),
            ("none", _("None")),
        )

    def queryset(self, request, queryset) -> QuerySet:
        now = timezone.now()

        if self.value() == "valid":
            return queryset.filter(
                Q(valid_from__lte=now) & Q(valid_until=None) | Q(valid_until__lt=now)
            )

        if self.value() == "invalid":
            return queryset.filter(valid_until__gte=now)

        if self.value() == "none":
            return queryset.filter(valid_from=None)

        return queryset


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    """Manage bank accounts"""

    list_display = ("iban", "owner_link", "last_used", "valid_from", "valid_until")
    list_filter = (ValidAccountFilter, "owner__profile__auto_renew")
    fields = (
        "created_at",
        "last_used",
        "owner",
        "iban",
        "bic",
        "initials",
        "last_name",
        "mandate_no",
        "valid_from",
        "valid_until",
        "signature",
    )
    readonly_fields = ("created_at",)
    search_fields = ("owner__username", "owner__first_name", "owner__last_name", "iban")
    autocomplete_fields = ("owner",)
    actions = ["set_last_used"]
    form = BankAccountAdminForm

    def owner_link(self, obj: BankAccount) -> str:
        if obj.owner:
            return format_html(
                "<a href='{}'>{}</a>",
                reverse("admin:auth_user_change", args=[obj.owner.pk]),
                obj.owner.get_full_name(),
            )
        return ""

    owner_link.admin_order_field = "owner"
    owner_link.short_description = _("owner")

    def set_last_used(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Set the last used date of selected accounts"""
        if request.user.has_perm("payments.change_bankaccount"):
            updated = services.update_last_used(queryset)
            _show_message(
                self,
                request,
                updated,
                message=_("Successfully updated %(count)d %(items)s."),
                error=_("The selected account(s) could not be updated."),
            )

    set_last_used.short_description = _("Update the last used date")

    def export_csv(self, request: HttpRequest, queryset: QuerySet) -> HttpResponse:
        response = HttpResponse(content_type="text/csv")
        response[
            "Content-Disposition"
        ] = 'attachment;\
                                           filename="accounts.csv"'
        writer = csv.writer(response)
        headers = [
            _("created"),
            _("name"),
            _("reference"),
            _("IBAN"),
            _("BIC"),
            _("valid from"),
            _("valid until"),
            _("signature"),
        ]
        writer.writerow([capfirst(x) for x in headers])
        for account in queryset:
            writer.writerow(
                [
                    account.created_at,
                    account.name,
                    account.mandate_no,
                    account.iban,
                    account.bic or "",
                    account.valid_from or "",
                    account.valid_until or "",
                    account.signature or "",
                ]
            )
        return response

    export_csv.short_description = _("Export")
