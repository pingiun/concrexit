"""thaliawebsite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/dev/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
import os.path

from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='index.html'), name='index'),
    url(r'^admin/', admin.site.urls),
    url(r'^members/', include('members.urls')),
    url(r'^nyi$', TemplateView.as_view(template_name='status/nyi.html'), name='#'),
    url(r'^association/', include([
        url(r'^committees/', include('committees.urls', namespace='committees')),
        url(r'^documents/', include('documents.urls', namespace='documents')),
        url(r'^sister-associations', TemplateView.as_view(template_name='singlepages/sister_associations.html'), name='sister-associations'),
    ])),
    url(r'^for-members/', include([
        url(r'^become-active', TemplateView.as_view(template_name='singlepages/become_active.html'), name='become-active'),
    ])),
    url(r'^contact$', TemplateView.as_view(template_name='singlepages/contact.html'), name='contact'),
    # Default login helpers
    url(r'^', include('django.contrib.auth.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
] + static(settings.MEDIA_URL,
           document_root=os.path.join(settings.MEDIA_ROOT, 'public'))
