import csv
from datetime import timedelta

from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required, login_required
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from .models import Event, Registration


@staff_member_required
@permission_required('events.change_event')
def admin_details(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    n = event.max_participants
    registrations = list(event.registration_set.filter(date_cancelled=None))
    cancellations = event.registration_set.exclude(date_cancelled=None)
    return render(request, 'events/admin/details.html', {
        'event': event,
        'registrations': registrations[:n],
        'waiting': registrations[n:] if n else [],
        'cancellations': cancellations,
    })


@staff_member_required
@permission_required('events.change_event')
def export(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    extra_fields = event.registrationinformationfield_set.all()
    registrations = event.registration_set.all()

    header_fields = (
        ['name', 'date', 'email'] + [field.name for field in extra_fields] +
        ['present', 'paid', 'status', 'date_cancelled'])

    rows = []
    capacity = event.max_participants
    for i, registration in enumerate(registrations):
        if registration.member:
            name = registration.member.get_full_name()
        else:
            name = registration.name
        status = 'registered'
        cancelled = None
        if registration.date_cancelled:
            if capacity is not None:
                capacity += 1
            status = 'cancelled'
            cancelled = timezone.localtime(registration.date_cancelled)
        elif capacity and i >= capacity:
            status = 'waiting'
        data = {
            'name': name,
            'date': timezone.localtime(registration.date),
            'paid': registration.paid,
            'present': registration.present,
            'email': (registration.member.user.email
                      if registration.member
                      else ''),
            'status': status,
            'date_cancelled': cancelled,
        }
        data.update({field['field'].name: field['value'] for field in
                     registration.registration_information()})
        rows.append(data)

    response = HttpResponse(content_type='text/csv')
    writer = csv.DictWriter(response, header_fields)
    writer.writeheader()

    def order(item):
        if item['status'] == 'cancelled':
            return item['date'] + timedelta(days=10000)
        elif item['status'] == 'registered':
            return item['date'] - timedelta(days=10000)
        else:
            return item['date']

    for row in sorted(rows, key=order):
        writer.writerow(row)

    response['Content-Disposition'] = (
        'attachment; filename="{}.csv"'.format(slugify(event.title)))
    return response


def index(request):
    upcoming_activity = Event.objects.filter(
        published=True,
        end__gte=timezone.now()
    ).order_by('end').first()

    return render(request, 'events/index.html', {
        'upcoming_activity': upcoming_activity
    })


def event(request, event_id):
    event = get_object_or_404(
        Event.objects.filter(published=True),
        pk=event_id
    )
    registrations = event.registration_set.filter(date_cancelled=None)

    context = {
        'event': event,
        'registrations': registrations,
        'user': request.user,
    }

    if event.max_participants:
        perc = 100.0 * len(registrations) / event.max_participants
        context['registration_percentage'] = perc

    try:
        registration = Registration.objects.get(
            event=event,
            member=request.user.member
        )
        context['registration'] = registration
    except Registration.DoesNotExist:
        pass

    return render(request, 'events/event.html', context)


@login_required
def registration(request, event_id, action=None):
    event = get_object_or_404(
        Event.objects.filter(published=True),
        pk=event_id
    )

    if event.registration_required():
        try:
            registration = Registration.objects.get(
                event=event,
                member=request.user.member
            )
        except Registration.DoesNotExist:
            registration = None

        success_message = None
        error_message = None
        show_fields = False
        if action == 'register':
            if event.has_fields():
                show_fields = True

            if registration is None:
                registration = Registration()
                registration.event = event
                registration.member = request.user.member
            elif registration.date_cancelled is not None:
                registration.date = timezone.now()
                registration.date_cancelled = None
            else:
                error_message = _("You were already registered.")

            if error_message is None:
                success_message = _("Registration successful")
        elif (action == 'update' and event.has_fields() and
                registration is not None):
            show_fields = True
        elif action == 'cancel':
            if (registration is not None and
                    registration.date_cancelled is None):
                registration.date_cancelled = timezone.now()
                success_message = _("Registration successfully cancelled")
            else:
                error_message = _("You were not registered for this event.")

        if show_fields:
            # saved = False
            #
            # if request.POST:
            #     form = AddExamForm(request.POST, request.FILES)
            #     if form.is_valid():
            #         saved = True
            #         obj = form.save(commit=False)
            #         obj.uploader = request.user
            #         obj.uploader_date = datetime.now()
            #         obj.save()
            #
            #         form = AddExamForm()
            #         form.exam_date = datetime.now()
            # else:
            #     obj = Exam()
            #     if id is not None:
            #         obj.course = Course.objects.get(id=id)
            #     form = AddExamForm(instance=obj)
            #     form.exam_date = datetime.now()

            context = {'event': event}
            return render(request, 'events/event_fields.html', context)
        else:
            if success_message is not None:
                messages.success(request, success_message)
            elif error_message is not None:
                messages.error(request, error_message)
            registration.save()

    return redirect(event)
