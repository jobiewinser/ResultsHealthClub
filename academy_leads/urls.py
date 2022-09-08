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
from django.urls import path
import academy_leads.views as academyleadsviews
import academy_leads.htmx as academyleadshtmx
urlpatterns = [
    path('', academyleadsviews.AcademyLeadsOverviewView.as_view(), name='academy-leads-overview'),
    path('mark-done/', academyleadshtmx.mark_done, name='mark-done' ),
    path('create-academy-lead/', academyleadshtmx.create_academy_lead, name='create-academy-lead' ),
    path('log-communication/', academyleadshtmx.log_communication, name='log-communication' ),
    path('add-booking/', academyleadshtmx.add_booking, name='add-booking' ),
    path('mark-arrived/', academyleadshtmx.mark_arrived, name='mark-arrived' ),
    path('mark-sold/', academyleadshtmx.mark_sold, name='mark-sold' ),
    
    path('academy-lead-get-modal-content/', academyleadshtmx.get_modal_content, name='academy-lead-get-modal-content' ),
    path('academy-lead-get-modal-content/<str:param1>/', academyleadshtmx.get_modal_content, name='academy-lead-get-modal-content' ),
    path('academy-lead-get-modal-content/<str:param1>/<str:param2>/', academyleadshtmx.get_modal_content, name='academy-lead-get-modal-content' ),
    
]
