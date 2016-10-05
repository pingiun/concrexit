from django.contrib import sitemaps
from django.urls import reverse

from . import models


class StaticViewSitemap(sitemaps.Sitemap):
    changefreq = 'daily'
    priority = 0.5

    def items(self):
        return ['education:books', 'education:courses']

    def location(self, item):
        return reverse(item)


class CourseSitemap(sitemaps.Sitemap):

    def items(self):
        return models.Course.objects.all()

    def location(self, item):
        return item.get_absolute_url()


sitemap = {
    'education-static': StaticViewSitemap,
    'education-courses': CourseSitemap,
}