"""jobiewebsite URL Configuration

The `urlpatterns` list routes URLs to views. For more inlistation please see:
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
from django.urls import path
import calendly.views as calendlyviews
urlpatterns = [
    path('calendly-webhooks/<str:guid>/', calendlyviews.Webhooks.as_view(), name='calendly-webhooks' ),
    path('calendly-booking-success/', calendlyviews.calendly_booking_success, name='calendly-booking-success' ),
    
]