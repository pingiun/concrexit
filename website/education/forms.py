from django.conf import settings
from django.forms import (
    ModelForm,
    DateField,
    SelectDateWidget,
    ModelChoiceField,
    ChoiceField
)

from .models import Exam, Summary, Course


class AddExamForm(ModelForm):
    exam_date = DateField(widget=SelectDateWidget())
    course = ModelChoiceField(
        queryset=Course.objects.order_by('name_' + settings.LANGUAGE_CODE),
        empty_label=None)
    type = ChoiceField(choices=Exam.EXAM_TYPES)

    class Meta:
        model = Exam
        fields = ('file', 'course', 'type', 'exam_date')


class AddSummaryForm(ModelForm):
    course = ModelChoiceField(
        queryset=Course.objects.order_by('name_' + settings.LANGUAGE_CODE),
        empty_label=None)

    class Meta:
        model = Summary
        fields = ('name', 'year', 'file', 'course', 'author')