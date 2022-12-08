"""jobiewebsite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.urls import path
import core.views as coreviews
handler500 = coreviews.handler500

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('campaign_leads.urls')),
    path('', include('core.urls')),
    path('', include('messaging.urls')),
    path('', include('whatsapp.urls')),
    path('', include('active_campaign.urls')),
    path('', include('analytics.urls')),
    path('', include('calendly.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    # path('twilio/', include('twilio.urls')),
    url(r'^hijack/', include('hijack.urls', namespace='hijack')),
]
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()