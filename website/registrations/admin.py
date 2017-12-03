from django.contrib import admin, messages
from django.contrib.admin.utils import model_ngettext
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from registrations import services

from .models import Entry, Payment, Registration, Renewal


def _show_message(admin, request, n, message, error):
    if n == 0:
        admin.message_user(request, error, messages.ERROR)
    else:
        admin.message_user(request, message % {
            "count": n,
            "items": model_ngettext(admin.opts, n)
        }, messages.SUCCESS)


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'status',
                    'created_at', 'payment_status')
    list_filter = ('status', 'programme', 'payment__processed',
                   'payment__amount')
    search_fields = ('first_name', 'last_name', 'email', 'phone_number',
                     'student_number',)
    date_hierarchy = 'created_at'
    fieldsets = (
        (_('Application information'), {
            'fields': ('created_at',
                       'updated_at',
                       'username',
                       'length',
                       'membership_type',
                       'status',
                       'remarks',)
        }),
        (_('Personal information'), {
            'fields': ('first_name',
                       'last_name',
                       'birthday',
                       'email',
                       'phone_number',)
        }),
        (_('Address'), {
            'fields': ('address_street',
                       'address_street2',
                       'address_postal_code',
                       'address_city',)
        }),
        (_('University information'), {
            'fields': ('student_number',
                       'programme',
                       'starting_year',)
        }),
    )
    actions = ['accept_selected', 'reject_selected']

    def changeform_view(self, request, object_id=None, form_url='',
                        extra_context=None):
        obj = None
        if (object_id is not None and
                request.user.has_perm('registrations.review_entries')):
            obj = Entry.objects.get(id=object_id)
            if not (obj.status == Entry.STATUS_REVIEW):
                obj = None
        return super().changeform_view(
            request, object_id, form_url, {'entry': obj})

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.has_perm('registrations.review_entries'):
            del(actions['accept_selected'])
            del(actions['reject_selected'])
        return actions

    def get_readonly_fields(self, request, obj=None):
        if obj is None or not (obj.status == Entry.STATUS_REJECTED or
                               obj.status == Entry.STATUS_ACCEPTED):
            return ['status', 'created_at', 'updated_at']
        else:
            return [field.name for field in self.model._meta.get_fields()
                    if field.editable]

    @staticmethod
    def name(obj):
        return obj.get_full_name()

    @staticmethod
    def payment_status(obj):
        try:
            payment = obj.payment
            processed_str = (_('Processed') if payment.processed else
                             _('Unprocessed'))
            return format_html('<a href="{link}">{title}</a>'
                               .format(link=payment.get_admin_url(),
                                       title=processed_str))
        except Payment.DoesNotExist:
            return '-'

    def reject_selected(self, request, queryset):
        if request.user.has_perm('registrations.review_entries'):
            rows_updated = services.reject_entries(queryset)
            _show_message(
                self, request, rows_updated,
                message=_("Successfully rejected %(count)d %(items)s."),
                error=_('The selected registration(s) could not be rejected.')
            )
    reject_selected.short_description = _('Reject selected registrations')

    def accept_selected(self, request, queryset):
        if request.user.has_perm('registrations.review_entries'):
            rows_updated = services.accept_entries(queryset)
            _show_message(
                self, request, rows_updated,
                message=_("Successfully accepted %(count)d %(items)s."),
                error=_('The selected registration(s) could not be accepted.')
            )
    accept_selected.short_description = _('Accept selected registrations')


@admin.register(Renewal)
class RenewalAdmin(RegistrationAdmin):
    list_display = ('name', 'email', 'status',
                    'created_at', 'payment_status',)
    list_filter = ('status', 'payment__processed', 'payment__amount')
    search_fields = ('member__first_name', 'member__last_name',
                     'member__email', 'member__profile__phone_number',
                     'member__profile__student_number',)
    date_hierarchy = 'created_at'
    fieldsets = (
                    (_('Application information'), {
                        'fields': (
                            'created_at',
                            'updated_at',
                            'length',
                            'membership_type',
                            'status',
                            'remarks',
                            'member',)
                    }),
    )

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if 'member' not in fields and obj is not None:
            return fields + ['member']
        return fields

    @staticmethod
    def name(obj):
        return obj.member.get_full_name()

    @staticmethod
    def email(obj):
        return obj.member.email


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('entry', 'created_at', 'amount',
                    'processed', 'processing_date', 'type')
    list_filter = ('processed', 'amount',)
    date_hierarchy = 'created_at'
    fields = ('created_at', 'entry', 'amount',
              'type', 'processed', 'processing_date')
    readonly_fields = ('created_at', 'amount', 'processed',
                       'type', 'entry', 'processing_date')
    actions = ['process_cash_selected', 'process_card_selected']

    def changeform_view(self, request, object_id=None, form_url='',
                        extra_context=None):
        obj = None
        if (object_id is not None and
                request.user.has_perm('registrations.process_payments')):
            obj = Payment.objects.get(id=object_id)
            if obj.processed:
                obj = None
        return super().changeform_view(
            request, object_id, form_url, {'payment': obj})

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.has_perm('registrations.process_payments'):
            del(actions['process_cash_selected'])
            del(actions['process_card_selected'])
        return actions

    def process_cash_selected(self, request, queryset):
        if request.user.has_perm('registrations.process_payments'):
            updated_payments = services.process_payment(queryset,
                                                        'cash_payment')
            self._process_feedback(request, updated_payments)
    process_cash_selected.short_description = _(
        'Process selected payments (cash)')

    def process_card_selected(self, request, queryset):
        if request.user.has_perm('registrations.process_payments'):
            updated_payments = services.process_payment(queryset,
                                                        'card_payment')
            self._process_feedback(request, updated_payments)
    process_card_selected.short_description = _(
        'Process selected payments (card)')

    def _process_feedback(self, request, updated_payments):
        rows_updated = len(updated_payments)
        _show_message(
            self, request, rows_updated,
            message=_("Successfully processed %(count)d %(items)s."),
            error=_('The selected payment(s) could not be processed.')
        )