"""Admin views provided by the payments package"""
import csv
import datetime

from django.contrib import messages
from django.contrib.admin.utils import model_ngettext
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.views import View

from members.models import Member
from payments import services
from .models import Payment, Batch, BankAccount


@method_decorator(staff_member_required, name='dispatch')
@method_decorator(permission_required('payments.process_payments'),
                  name='dispatch', )
class PaymentAdminView(View):
    """
    View that processes a payment
    """
    def post(self, request, *args, **kwargs):
        payment = Payment.objects.filter(pk=kwargs['pk'])

        if not ('type' in request.POST):
            return redirect('admin:payments_payment_change', kwargs['pk'])

        result = services.process_payment(
            payment, request.member, request.POST['type']
        )

        if len(result) > 0:
            messages.success(request, _('Successfully processed %s.') %
                             model_ngettext(payment, 1))
        else:
            messages.error(request, _('Could not process %s.') %
                           model_ngettext(payment, 1))

        if 'next' in request.POST:
            return redirect(request.POST['next'])

        return redirect('admin:payments_payment_change', kwargs['pk'])


@method_decorator(staff_member_required, name='dispatch')
@method_decorator(permission_required('payments.process_batches'),
                  name='dispatch', )
class BatchAdminView(View):
    """
    View that processes a batch
    """
    def post(self, request, *args, **kwargs):
        batch = Batch.objects.get(pk=kwargs['pk'])

        if batch.processed:
            messages.error(request, _('{} already processed.').format(
                model_ngettext(batch, 1)))
        else:
            batch.processed = True
            batch.save()
            messages.success(request, _('Successfully processed {}.').format(
                model_ngettext(batch, 1)))

        if 'next' in request.POST:
            return redirect(request.POST['next'])

        return redirect('admin:payments_batch_change', kwargs['pk'])


@method_decorator(staff_member_required, name='dispatch')
@method_decorator(permission_required('payments.process_batches'),
                  name='dispatch', )
class BatchExportAdminView(View):
    """
    View tht exports a batch
    """
    def post(self, request, *args, **kwargs):
        batch = Batch.objects.get(pk=kwargs['pk'])

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment;filename="batch.csv"'
        writer = csv.writer(response)
        headers = [_('Account holder name'), _('IBAN'), _('Mandate id'),
                   _('Amount'), _('Description'), _('Mandate date'), ]
        writer.writerow([capfirst(x) for x in headers])

        memeber_rows = batch.payments_set.values('paid_by').annotate(
            total=Sum('amount'))

        print(memeber_rows)

        for row in memeber_rows:
            member: Member = Member.objects.get(id=row['paid_by'])
            bankaccount: BankAccount = member.bank_accounts.last()
            print(member, bankaccount)
            writer.writerow([
                member.get_full_name(),
                bankaccount.iban,
                bankaccount.mandate_no,
                row['total'],
                batch.description,
                bankaccount.valid_from
            ])
        return response


@method_decorator(staff_member_required, name='dispatch')
@method_decorator(permission_required('payments.process_batches'),
                  name='dispatch', )
class BatchNewFilledAdminView(View):
    """
    View tht exports a batch
    """
    def get(self, request, *args, **kwargs):
        batch = Batch()
        batch.save()

        now = datetime.datetime.utcnow()
        last_month_start = (datetime.datetime(now.year, now.month, 1) - datetime.timedelta(days=1)).replace(day=1)
        last_month_end = datetime.datetime(now.year, now.month, 1, 23, 59) - datetime.timedelta(days=1)
        payments = Payment.objects.filter(
            type=Payment.TPAY,
            batch=None,
            processing_date__gte=last_month_start,
            # processing_date__lte=last_month_end,
        )

        payments.update(batch=batch)

        return redirect('admin:payments_batch_change', object_id=batch.id)
