from django.db import models
from django.core.validators import RegexValidator, URLValidator
from django.urls import reverse

from utils.translation import MultilingualField, ModelTranslateMeta
from tinymce.models import HTMLField


class Partner(models.Model):
    is_active = models.BooleanField(default=False)
    is_main_partner = models.BooleanField(default=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    link = models.CharField(
        max_length=255,
        blank=True,
        validators=[URLValidator()]
    )
    company_profile = HTMLField(blank=True)
    logo = models.ImageField(upload_to='public/partners/logos/')
    site_header = models.ImageField(
        upload_to='public/partners/headers/',
        null=True,
        blank=True
    )

    address = models.CharField(max_length=100, validators=[
        RegexValidator(
            regex=(r'^([1-9][e][\s])*([ëéÉËa-zA-Z]'
                   '+(([\.][\s])|([\s]))?)+[1-9][0-9]'
                   '*(([-][1-9][0-9]*)|([\s]?[ëéÉËa-zA-Z]+))?$'),
            message='Enter a valid address')
    ])
    zip_code = models.CharField(max_length=12, validators=[
        RegexValidator(
            regex=r'^[1-9][0-9]{3}[\s]?[A-Za-z]{2}$',
            message='Enter a valid zip code'
        )
    ])
    city = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        if self.is_main_partner:
            self._reset_main_partner()

        super(Partner, self).save(*args, **kwargs)

    def _reset_main_partner(self):
        try:
            current_main_partner = Partner.objects.get(is_main_partner=True)
            if self != current_main_partner:
                current_main_partner.is_main_partner = False
                current_main_partner.save()
        except Partner.DoesNotExist:
            pass

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('partner', args=(self.slug,))


class PartnerImage(models.Model):
    partner = models.ForeignKey(
        Partner,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to='public/partners/images/')

    def __str__(self):
        return 'image of {}'.format(self.partner.name)


class VacancyCategory(models.Model, metaclass=ModelTranslateMeta):
    name = MultilingualField(models.CharField, max_length=30)
    slug = models.SlugField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Vanancy Categories'


class Vacancy(models.Model):
    title = models.CharField(max_length=255)
    description = HTMLField(blank=True)
    link = models.CharField(
        max_length=255,
        blank=True,
        validators=[URLValidator()]
    )

    partner = models.ForeignKey(
        Partner,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="When you use a partner, the company name and logo " +
                  "below will not be used."
    )

    company_name = models.CharField(max_length=255, blank=True)
    company_logo = models.ImageField(
        upload_to='public/partners/vacancy-logos/',
        null=True,
        blank=True
    )

    categories = models.ManyToManyField(VacancyCategory, blank=True)

    def get_company_name(self):
        if self.partner:
            return self.partner.name
        return self.company_name

    def get_company_logo(self):
        if self.partner:
            return self.partner.logo
        return self.company_logo

    def __str__(self):
        return self.get_company_name() + ' - ' + self.title

    class Meta:
        verbose_name_plural = 'Vacancies'