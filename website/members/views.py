"""Views provided by the members package"""
import json
from datetime import date, datetime

from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q, QuerySet
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import (ListView, DetailView, UpdateView,
                                  CreateView)
from django.views.generic.base import TemplateResponseMixin, View, TemplateView
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response

import pizzas.services
from members import services, emails
from members.decorators import membership_required
from members.models import EmailChange, Membership, Member, Profile
from utils.snippets import datetime_to_lectureyear
from . import models
from .forms import ProfileForm
from .services import member_achievements
from .services import member_societies


class ObtainThaliaAuthToken(ObtainAuthToken):
    """
    Custom override of the AuthToken view to force lowercase the username
    """

    def post(self, request, *args, **kwargs) -> HttpResponse:
        serializer = self.serializer_class(data={
            'username': request.data.get('username').lower()
            if 'username' in request.data else None,
            'password': request.data.get('password')
        }, context={'request': request})

        if not serializer.is_valid():
            return HttpResponse('Unauthorized', status=401)

        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})


@method_decorator(login_required, 'dispatch')
@method_decorator(membership_required, 'dispatch')
class MembersIndex(ListView):
    """
    View that renders the members overview
    """
    model = Member
    paginate_by = 28
    template_name = 'members/index.html'
    context_object_name = 'members'
    keywords = None
    query_filter = ''
    year_range = []

    def setup(self, request, *args, **kwargs) -> None:
        super().setup(request, *args, **kwargs)
        current_lectureyear = datetime_to_lectureyear(date.today())
        self.year_range = list(reversed(range(current_lectureyear - 5,
                                              current_lectureyear + 1)))
        self.keywords = request.GET.get('keywords', '').split() or None
        self.query_filter = kwargs.get('filter', None)

    def get_queryset(self) -> QuerySet:
        memberships_query = Q(until__gt=datetime.now()) | Q(until=None)
        members_query = ~Q(id=None)

        if self.query_filter and self.query_filter.isdigit():
            members_query &= Q(profile__starting_year=int(self.query_filter))
            memberships_query &= Q(type=Membership.MEMBER)
        elif self.query_filter == 'older':
            members_query &= Q(profile__starting_year__lt=self.year_range[-1])
            memberships_query &= Q(type=Membership.MEMBER)
        elif self.query_filter == 'former':
            # Filter out all current active memberships
            memberships_query &= (Q(type=Membership.MEMBER) |
                                  Q(type=Membership.HONORARY))
            memberships = Membership.objects.filter(memberships_query)
            members_query &= ~Q(pk__in=memberships.values('user__pk'))
        # Members_query contains users that are not currently (honorary)member
        elif self.query_filter == 'benefactors':
            memberships_query &= Q(type=Membership.BENEFACTOR)
        elif self.query_filter == 'honorary':
            memberships_query = Q(until__gt=datetime.now().date()) | Q(
                until=None)
            memberships_query &= Q(type=Membership.HONORARY)

        if self.keywords:
            for key in self.keywords:
                # Works because relevant options all have `nick` in their key
                members_query &= (
                    (Q(profile__nickname__icontains=key) &
                     Q(profile__display_name_preference__contains='nick')) |
                    Q(first_name__icontains=key) |
                    Q(last_name__icontains=key) |
                    Q(username__icontains=key))

        if self.query_filter == 'former':
            memberships_query = (Q(type=Membership.MEMBER) |
                                 Q(type=Membership.HONORARY))
            memberships = Membership.objects.filter(memberships_query)
            all_memberships = Membership.objects.all()
            # Only keep members that were once members, or are legacy users
            # that do not have any memberships at all
            members_query &= (Q(pk__in=memberships.values('user__pk')) |
                              ~Q(pk__in=all_memberships.values('user__pk')))
        else:
            memberships = Membership.objects.filter(memberships_query)
            members_query &= Q(pk__in=memberships.values('user__pk'))
        return Member.objects.filter(members_query).order_by('first_name')

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        page = context['page_obj'].number
        paginator = context['paginator']

        page_range = range(1, paginator.num_pages + 1)
        if paginator.num_pages > 7:
            if page > 3:
                page_range_end = paginator.num_pages
                if page + 3 <= paginator.num_pages:
                    page_range_end = page + 3

                page_range = range(page - 2, page_range_end)
                while page_range.stop - page_range.start < 5:
                    page_range = range(page_range.start - 1, page_range.stop)
            else:
                page_range = range(1, 6)

        context.update({
            'filter': self.query_filter,
            'page_range': page_range,
            'year_range': self.year_range,
            'keywords': self.keywords
        })

        return context


@method_decorator(login_required, 'dispatch')
class ProfileDetailView(DetailView):
    """
    View that renders a member's profile
    """
    context_object_name = 'member'
    model = Member
    template_name = 'members/user/profile.html'

    def setup(self, request, *args, **kwargs) -> None:
        if 'pk' not in kwargs:
            kwargs['pk'] = request.member.pk
        super().setup(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        member = context['member']

        achievements = member_achievements(member)
        societies = member_societies(member)

        membership = member.current_membership
        membership_type = _("Unknown membership history")
        if membership:
            membership_type = membership.get_type_display()
        elif member.has_been_honorary_member():
            membership_type = _("Former honorary member")
        elif member.has_been_member():
            membership_type = _("Former member")
        elif member.latest_membership:
            membership_type = _("Former benefactor")

        context.update({
            'achievements': achievements,
            'societies': societies,
            'membership_type': membership_type,
        })

        return context


@method_decorator(login_required, 'dispatch')
class UserAccountView(TemplateView):
    """
    View that renders the account options page
    """
    template_name = 'members/user/index.html'


@method_decorator(login_required, 'dispatch')
class UserProfileUpdateView(SuccessMessageMixin, UpdateView):
    """
    View that allows a user to update their profile
    """
    template_name = 'members/user/edit_profile.html'
    model = Profile
    form_class = ProfileForm
    success_url = reverse_lazy('members:edit-profile')
    success_message = _('Your profile has been updated successfully.')

    def get_object(self, queryset=None) -> Profile:
        return get_object_or_404(models.Profile, user=self.request.user)


@method_decorator(login_required, 'dispatch')
class StatisticsView(TemplateView):
    """
    View that renders the statistics page
    """
    template_name = 'members/statistics.html'

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        member_types = [t[0] for t in Membership.MEMBERSHIP_TYPES]
        total = models.Member.current_members.count()

        context.update({
            "total_members": total,
            "statistics": json.dumps({
                "cohort_sizes": services.gen_stats_year(member_types),
                "member_type_distribution":
                    services.gen_stats_member_type(member_types),
                "total_pizza_orders": pizzas.services.gen_stats_pizza_orders(),
                "current_pizza_orders":
                    pizzas.services.gen_stats_current_pizza_orders(),
            })
        })

        return context


@method_decorator(login_required, name='dispatch')
class EmailChangeFormView(CreateView):
    """
    View that renders the email change form
    """
    model = EmailChange
    fields = ['email', 'member']
    template_name = 'members/user/email_change.html'

    def get_initial(self) -> dict:
        initial = super().get_initial()
        initial['email'] = self.request.member.email
        return initial

    def post(self, request, *args, **kwargs) -> HttpResponse:
        request.POST = request.POST.dict()
        request.POST['member'] = request.member.pk
        return super().post(request, *args, **kwargs)

    def form_valid(self, form) -> HttpResponse:
        change_request = form.save()
        emails.send_email_change_confirmation_messages(change_request)
        return TemplateResponse(
            request=self.request,
            template='members/user/email_change_requested.html')


@method_decorator(login_required, name='dispatch')
class EmailChangeConfirmView(View, TemplateResponseMixin):
    """
    View that renders an HTML template and confirms the old email address
    """
    template_name = 'members/user/email_change_confirmed.html'

    def get(self, request, *args, **kwargs) -> HttpResponse:
        if not EmailChange.objects.filter(confirm_key=kwargs['key']).exists():
            raise Http404

        change_request = EmailChange.objects.get(confirm_key=kwargs['key'])

        services.confirm_email_change(change_request)

        return self.render_to_response({})


@method_decorator(login_required, name='dispatch')
class EmailChangeVerifyView(View, TemplateResponseMixin):
    """
    View that renders an HTML template and verifies the new email address
    """
    template_name = 'members/user/email_change_verified.html'

    def get(self, request, *args, **kwargs) -> HttpResponse:
        if not EmailChange.objects.filter(verify_key=kwargs['key']).exists():
            raise Http404

        change_request = EmailChange.objects.get(verify_key=kwargs['key'])

        services.verify_email_change(change_request)

        return self.render_to_response({})
