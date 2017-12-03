from unittest import mock

from django.core import mail
from django.template import loader
from django.template.defaultfilters import floatformat
from django.test import TestCase
from django.urls import reverse
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from members.models import Member, Profile
from registrations import emails
from registrations.emails import _send_email
from registrations.models import Payment, Registration, Renewal
from thaliawebsite.settings import settings


class EmailsTest(TestCase):
    def test_board_notification_address(self):
        self.assertEqual(settings.BOARD_NOTIFICATION_ADDRESS, 'info@thalia.nu')

    @mock.patch('registrations.emails._send_email')
    def test_send_registration_email_confirmation(self, send_email):
        reg = Registration(
            language='en',
            email='test@example.org',
            first_name='John',
            last_name='Doe',
            pk=0,
        )

        emails.send_registration_email_confirmation(reg)

        with translation.override(reg.language):
            send_email.assert_called_once_with(
                reg.email,
                _('Confirm email address'),
                'registrations/email/registration_confirm_mail.txt',
                {
                    'name': reg.get_full_name(),
                    'confirm_link': '{}{}'.format(
                        'https://thalia.nu',
                        reverse('registrations:confirm-email',
                                args=[reg.pk])
                    )
                }
            )

    @mock.patch('registrations.emails._send_email')
    def test_send_registration_accepted_message(self, send_email):
        reg = Registration(
            language='en',
            email='test@example.org',
            first_name='John',
            last_name='Doe',
            pk=0,
        )

        payment = Payment(
            amount=2,
        )

        emails.send_registration_accepted_message(reg, payment)

        with translation.override(reg.language):
            send_email.assert_called_once_with(
                reg.email,
                _('Registration accepted'),
                'registrations/email/registration_accepted.txt',
                {
                    'name': reg.get_full_name(),
                    'fees': floatformat(payment.amount, 2)
                }
            )

    @mock.patch('registrations.emails._send_email')
    def test_send_registration_rejected_message(self, send_email):
        reg = Registration(
            language='en',
            email='test@example.org',
            first_name='John',
            last_name='Doe',
            pk=0,
        )

        emails.send_registration_rejected_message(reg)

        with translation.override(reg.language):
            send_email.assert_called_once_with(
                reg.email,
                _('Registration rejected'),
                'registrations/email/registration_rejected.txt',
                {
                    'name': reg.get_full_name()
                }
            )

    @mock.patch('registrations.emails._send_email')
    def test_send_new_registration_board_message(self, send_email):
        entry = Registration(
            language='en',
            email='test@example.org',
            first_name='John',
            last_name='Doe',
            pk=0,
        )
        entry.registration = entry

        emails.send_new_registration_board_message(entry)

        send_email.assert_called_once_with(
            settings.BOARD_NOTIFICATION_ADDRESS,
            'New registration',
            'registrations/email/registration_board.txt',
            {
                'name': entry.registration.get_full_name(),
                'url': reverse('admin:registrations_registration_change',
                               args=[entry.registration.pk])
            }
        )

        entry.registration = None
        emails.send_new_registration_board_message(entry)

    @mock.patch('registrations.emails._send_email')
    def test_send_renewal_accepted_message(self, send_email):
        member = Member(
            email="test@example.org",
            first_name='John',
            last_name='Doe',
            profile=Profile(
                language='en'
            )
        )

        renewal = Renewal(
            pk=0,
            member=member
        )

        payment = Payment(
            amount=2,
        )

        emails.send_renewal_accepted_message(renewal, payment)

        with translation.override(renewal.member.profile.language):
            send_email.assert_called_once_with(
                renewal.member.email,
                _('Renewal accepted'),
                'registrations/email/renewal_accepted.txt',
                {
                    'name': renewal.member.get_full_name(),
                    'fees': floatformat(payment.amount, 2)
                }
            )

    @mock.patch('registrations.emails._send_email')
    def test_send_renewal_rejected_message(self, send_email):
        member = Member(
            email="test@example.org",
            first_name='John',
            last_name='Doe',
            profile=Profile(
                language='en'
            )
        )

        renewal = Renewal(
            pk=0,
            member=member
        )

        emails.send_renewal_rejected_message(renewal)

        with translation.override(renewal.member.profile.language):
            send_email.assert_called_once_with(
                renewal.member.email,
                _('Registration rejected'),
                'registrations/email/renewal_rejected.txt',
                {
                    'name': renewal.member.get_full_name()
                }
            )

    @mock.patch('registrations.emails._send_email')
    def test_send_renewal_complete_message(self, send_email):
        member = Member(
            email="test@example.org",
            first_name='John',
            last_name='Doe',
            profile=Profile(
                language='en'
            )
        )

        renewal = Renewal(
            pk=0,
            member=member
        )

        emails.send_renewal_complete_message(renewal)

        with translation.override(renewal.member.profile.language):
            send_email.assert_called_once_with(
                renewal.member.email,
                _('Renewal successful'),
                'registrations/email/renewal_complete.txt',
                {
                    'name': renewal.member.get_full_name()
                }
            )

    @mock.patch('registrations.emails._send_email')
    def test_send_new_renewal_board_message(self, send_email):
        member = Member(
            email="test@example.org",
            first_name='John',
            last_name='Doe',
            profile=Profile(
                language='en'
            )
        )

        renewal = Renewal(
            pk=0,
            member=member
        )

        emails.send_new_renewal_board_message(renewal)

        send_email.assert_called_once_with(
            settings.BOARD_NOTIFICATION_ADDRESS,
            'New renewal',
            'registrations/email/renewal_board.txt',
            {
                'name': renewal.member.get_full_name(),
                'url': reverse('admin:registrations_renewal_change',
                               args=[renewal.pk])
            }
        )

    def test_send_email(self):
        _send_email(
            subject='Subject',
            to='test@example.org',
            body_template='registrations/email/renewal_board.txt',
            context={
                'name': 'name',
                'url': '',
            }
        )

        self.assertEqual(mail.outbox[0].subject, '[THALIA] Subject')
        self.assertEqual(mail.outbox[0].to, ['test@example.org'])
        self.assertEqual(mail.outbox[0].body, loader.render_to_string(
            'registrations/email/renewal_board.txt', {
                'name': 'name',
                'url': '',
            }))