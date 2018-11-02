import datetime

from django.contrib.auth.models import Permission
from django.core import mail
from django.test import Client, TestCase
from django.utils import timezone

from activemembers.models import Committee, MemberGroupMembership
from events.models import (Event, Registration,
                           RegistrationInformationField,
                           BooleanRegistrationInformation,
                           IntegerRegistrationInformation,
                           TextRegistrationInformation)
from mailinglists.models import MailingList
from members.models import Member


class AdminTest(TestCase):
    """Tests for admin views"""

    fixtures = ['members.json', 'member_groups.json']

    @classmethod
    def setUpTestData(cls):
        cls.committee = Committee.objects.get(pk=1)
        cls.event = Event.objects.create(
            pk=1,
            organiser=cls.committee,
            title_nl='testevenement',
            title_en='testevent',
            description_en='desc',
            description_nl='besch',
            published=True,
            start=(timezone.now() + datetime.timedelta(hours=1)),
            end=(timezone.now() + datetime.timedelta(hours=2)),
            location_en='test location',
            location_nl='test locatie',
            map_location='test map location',
            price=0.00,
            fine=0.00)
        cls.member = Member.objects.filter(last_name="Wiggers").first()
        cls.permission_change_event = Permission.objects.get(
            content_type__model='event',
            codename='change_event')
        cls.permission_override_orga = Permission.objects.get(
            content_type__model='event',
            codename='override_organiser')
        cls.member.user_permissions.add(cls.permission_change_event)
        cls.member.is_superuser = False
        cls.member.save()

    def setUp(self):
        self.client.force_login(self.member)

    def _remove_event_permission(self):
        self.member.user_permissions.remove(self.permission_change_event)

    def _add_override_organiser_permission(self):
        self.member.user_permissions.add(self.permission_override_orga)

    def test_admin_details_need_change_event_access(self):
        """I need the event.change_event permission to do stuff"""
        self._remove_event_permission()
        response = self.client.get('/events/admin/1/')
        self.assertEqual(302, response.status_code)
        self.assertTrue(response.url.startswith('/login/'))

    def test_admin_details_organiser_denied(self):
        response = self.client.get('/events/admin/1/')
        self.assertEqual(403, response.status_code)

    def test_admin_details_organiser_allowed(self):
        MemberGroupMembership.objects.create(
            member=self.member,
            group=self.committee)
        response = self.client.get('/events/admin/1/')
        self.assertEqual(200, response.status_code)

    def test_admin_details_override_organiser_allowed(self):
        self._add_override_organiser_permission()
        response = self.client.get('/events/admin/1/')
        self.assertEqual(200, response.status_code)

    def test_modeladmin_change_organiser_allowed(self):
        """Change event as an organiser

        If I'm an organiser I should be allowed access
        """
        MemberGroupMembership.objects.create(
            member=self.member,
            group=self.committee)
        response = self.client.get('/admin/events/event/1/change/')
        self.assertEqual(200, response.status_code)

    def test_modeladmin_change_override_organiser_allowed(self):
        """Test the override organiser permission for changing events

        If I'm allowed to override organiser restrictions..
        """
        self._add_override_organiser_permission()
        response = self.client.get('/admin/events/event/1/change/')
        self.assertEqual(200, response.status_code)

    def test_modeladmin_change_organiser_no_permissions_denied(self):
        """Committee members without change permissions are banned

        If I'm an organiser, but don't have perms I should not
        be allowed access
        """
        self._remove_event_permission()
        MemberGroupMembership.objects.create(
            member=self.member,
            group=self.committee)
        response = self.client.get('/admin/events/event/1/change/')
        self.assertEqual(403, response.status_code)

    def test_modeladmin_change_superuser_allowed(self):
        """Superuser should be allowed access always"""
        self.member.is_superuser = True
        self.member.save()
        response = self.client.get('/admin/events/event/1/change/')
        self.assertEqual(200, response.status_code)
        self.assertIn('Change event', str(response.content))

    def test_modeladmin_change_organiser_denied(self):
        """If I'm not an organiser I should not be allowed access"""
        response = self.client.get('/admin/events/event/1/change/')
        self.assertEqual(200, response.status_code)
        self.assertIn('View event', str(response.content))


class RegistrationTest(TestCase):
    """Tests for registration view"""

    fixtures = ['members.json', 'member_groups.json']

    @classmethod
    def setUpTestData(cls):
        cls.mailinglist = MailingList.objects.create(
            name="testmail"
        )
        cls.committee = Committee.objects.create(
            name_nl="commissie",
            name_en="committee",
            contact_mailinglist=cls.mailinglist
        )
        cls.event = Event.objects.create(
            pk=1,
            organiser=cls.committee,
            title_nl='testevene',
            title_en='testevent',
            description_en='desc',
            description_nl='besch',
            published=True,
            start=(timezone.now() + datetime.timedelta(hours=1)),
            end=(timezone.now() + datetime.timedelta(hours=2)),
            location_en='test location',
            location_nl='test locatie',
            map_location='test map location',
            price=0.00,
            fine=0.00)
        cls.member = Member.objects.filter(last_name="Wiggers").first()

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.member)

    def test_registration_register_not_required(self):
        response = self.client.post('/events/1/registration/register/',
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event.participants.count(), 0)

    def test_registration_register(self):
        self.event.registration_start = (timezone.now() -
                                         datetime.timedelta(hours=1))
        self.event.registration_end = (timezone.now() +
                                       datetime.timedelta(hours=1))
        self.event.cancel_deadline = (timezone.now() +
                                      datetime.timedelta(hours=1))
        self.event.save()
        response = self.client.post('/events/1/registration/register/',
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event.participants.count(), 1)
        self.assertEqual(
            self.event.registration_set.first().member, self.member)

    def test_registration_register_twice(self):
        self.event.registration_start = (timezone.now() -
                                         datetime.timedelta(hours=1))
        self.event.registration_end = (timezone.now() +
                                       datetime.timedelta(hours=1))
        self.event.cancel_deadline = (timezone.now() +
                                      datetime.timedelta(hours=1))
        self.event.save()
        response = self.client.post('/events/1/registration/register/',
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.post('/events/1/registration/register/',
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event.participants.count(), 1)

    def test_registration_register_closed(self):
        self.event.registration_start = (timezone.now() -
                                         datetime.timedelta(hours=2))
        self.event.registration_end = (timezone.now() -
                                       datetime.timedelta(hours=1))
        self.event.cancel_deadline = (timezone.now() +
                                      datetime.timedelta(hours=1))
        self.event.save()
        response = self.client.post('/events/1/registration/register/',
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event.participants.count(), 0)

    def test_registration_cancel(self):
        self.event.registration_start = (timezone.now() -
                                         datetime.timedelta(hours=1))
        self.event.registration_end = (timezone.now() +
                                       datetime.timedelta(hours=1))
        self.event.cancel_deadline = (timezone.now() +
                                      datetime.timedelta(hours=1))
        self.event.save()
        Registration.objects.create(event=self.event, member=self.member)
        response = self.client.post('/events/1/registration/cancel/',
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event.participants.count(), 0)

    def test_registration_register_no_fields(self):
        self.event.registration_start = (timezone.now() -
                                         datetime.timedelta(hours=1))
        self.event.registration_end = (timezone.now() +
                                       datetime.timedelta(hours=1))
        self.event.cancel_deadline = (timezone.now() +
                                      datetime.timedelta(hours=1))
        self.event.save()

        field1 = RegistrationInformationField.objects.create(
            pk=1,
            event=self.event,
            type=RegistrationInformationField.BOOLEAN_FIELD,
            name_en="test bool",
            name_nl="test bool",
            required=False)

        field2 = RegistrationInformationField.objects.create(
            pk=2,
            event=self.event,
            type=RegistrationInformationField.INTEGER_FIELD,
            name_en="test int",
            name_nl="test int",
            required=False)

        field3 = RegistrationInformationField.objects.create(
            pk=3,
            event=self.event,
            type=RegistrationInformationField.TEXT_FIELD,
            name_en="test text",
            name_nl="test text",
            required=False)

        response = self.client.post('/events/1/registration/register/',
                                    {'info_field_1': True,
                                     'info_field_2': 42,
                                     'info_field_3': "text"},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(self.event.participants.count(), 1)
        registration = self.event.registration_set.first()
        self.assertEqual(field1.get_value_for(registration), None)
        self.assertEqual(field2.get_value_for(registration), None)
        self.assertEqual(field3.get_value_for(registration), None)

    def test_registration_missing_fields(self):
        self.event.registration_start = (timezone.now() -
                                         datetime.timedelta(hours=1))
        self.event.registration_end = (timezone.now() +
                                       datetime.timedelta(hours=1))
        self.event.cancel_deadline = (timezone.now() +
                                      datetime.timedelta(hours=1))
        self.event.save()

        RegistrationInformationField.objects.create(
            pk=1,
            event=self.event,
            type=RegistrationInformationField.BOOLEAN_FIELD,
            name_en="test bool",
            name_nl="test bool",
            required=False)

        RegistrationInformationField.objects.create(
            pk=2,
            event=self.event,
            type=RegistrationInformationField.INTEGER_FIELD,
            name_en="test int",
            name_nl="test int",
            required=False)

        RegistrationInformationField.objects.create(
            pk=3,
            event=self.event,
            type=RegistrationInformationField.TEXT_FIELD,
            name_en="test text",
            name_nl="test text",
            required=False)

        response = self.client.post('/events/1/registration/register/',
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        template_names = [template.name for template in response.templates]
        self.assertIn('events/registration.html', template_names)
        self.assertEqual(self.event.participants.count(), 1)

    def test_registration_register_fields_required(self):
        self.event.registration_start = (timezone.now() -
                                         datetime.timedelta(hours=1))
        self.event.registration_end = (timezone.now() +
                                       datetime.timedelta(hours=1))
        self.event.cancel_deadline = (timezone.now() +
                                      datetime.timedelta(hours=1))
        self.event.save()

        RegistrationInformationField.objects.create(
            event=self.event,
            type=RegistrationInformationField.TEXT_FIELD,
            name_en="test",
            name_nl="test",
            required=True)

        response = self.client.post('/events/1/registration/register/',
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        template_names = [template.name for template in response.templates]
        self.assertIn('events/registration.html', template_names)
        self.assertEqual(self.event.participants.count(), 1)

    def test_registration_update_form_load_not_changes_fields(self):
        self.event.registration_start = (timezone.now() -
                                         datetime.timedelta(hours=1))
        self.event.registration_end = (timezone.now() +
                                       datetime.timedelta(hours=1))
        self.event.cancel_deadline = (timezone.now() +
                                      datetime.timedelta(hours=1))
        self.event.save()

        field1 = RegistrationInformationField.objects.create(
            pk=1,
            event=self.event,
            type=RegistrationInformationField.BOOLEAN_FIELD,
            name_en="test bool",
            name_nl="test bool",
            required=False)

        field2 = RegistrationInformationField.objects.create(
            pk=2,
            event=self.event,
            type=RegistrationInformationField.INTEGER_FIELD,
            name_en="test int",
            name_nl="test int",
            required=False)

        field3 = RegistrationInformationField.objects.create(
            pk=3,
            event=self.event,
            type=RegistrationInformationField.TEXT_FIELD,
            name_en="test text",
            name_nl="test text",
            required=False)

        registration = Registration.objects.create(
            event=self.event, member=self.member)
        BooleanRegistrationInformation.objects.create(
            registration=registration, field=field1, value=True)
        IntegerRegistrationInformation.objects.create(
            registration=registration, field=field2, value=42)
        TextRegistrationInformation.objects.create(
            registration=registration, field=field3, value="text")

        # as if there is a csrf token
        response = self.client.get('/events/1/registration/',
                                   follow=True)
        self.assertEqual(response.status_code, 200)

        registration = self.event.registration_set.first()
        self.assertEqual(field1.get_value_for(registration), True)
        self.assertEqual(field2.get_value_for(registration), 42)
        self.assertEqual(field3.get_value_for(registration), 'text')

    def test_registration_update_form_post_changes_fields(self):
        self.event.registration_start = (timezone.now() -
                                         datetime.timedelta(hours=1))
        self.event.registration_end = (timezone.now() +
                                       datetime.timedelta(hours=1))
        self.event.cancel_deadline = (timezone.now() +
                                      datetime.timedelta(hours=1))
        self.event.save()

        field1 = RegistrationInformationField.objects.create(
            pk=1,
            event=self.event,
            type=RegistrationInformationField.BOOLEAN_FIELD,
            name_en="test bool",
            name_nl="test bool",
            required=False)

        field2 = RegistrationInformationField.objects.create(
            pk=2,
            event=self.event,
            type=RegistrationInformationField.INTEGER_FIELD,
            name_en="test int",
            name_nl="test int",
            required=False)

        field3 = RegistrationInformationField.objects.create(
            pk=3,
            event=self.event,
            type=RegistrationInformationField.TEXT_FIELD,
            name_en="test text",
            name_nl="test text",
            required=False)

        response = self.client.post('/events/1/registration/register/',
                                    {'info_field_1': True,
                                     'info_field_2': 42,
                                     'info_field_3': 'text',
                                     'csrf': 'random'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/events/1/registration/',
                                    {'info_field_1': False,
                                     'info_field_2': 1337,
                                     'info_field_3': 'no text',
                                     'csrf': 'random'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(self.event.participants.count(), 1)
        registration = self.event.registration_set.first()
        self.assertEqual(field1.get_value_for(registration), False)
        self.assertEqual(field2.get_value_for(registration), 1337)
        self.assertEqual(field3.get_value_for(registration), 'no text')

    def test_registration_cancel_after_deadline_notification(self):
        self.event.registration_start = (timezone.now() -
                                         datetime.timedelta(hours=2))
        self.event.registration_end = (timezone.now() -
                                       datetime.timedelta(hours=1))
        self.event.cancel_deadline = (timezone.now() -
                                      datetime.timedelta(hours=1))
        self.event.send_cancel_email = True
        self.event.save()
        Registration.objects.create(event=self.event, member=self.member)
        response = self.client.post('/events/1/registration/cancel/',
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event.participants.count(), 0)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.event.organiser.
                         contact_mailinglist.name + "@thalia.nu"])
