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
    path('academy-leads/booking-and-calender/', academyleadsviews.AcademyBookingsOverviewView.as_view(), name='academy-booking-overview'),
    path('', academyleadsviews.AcademyLeadsOverviewView.as_view(), name='default'),
    path('academy-leads/leads-and-calls/', academyleadsviews.AcademyLeadsOverviewView.as_view(), name='academy-leads-overview'),    
    path('configuration/whatsapp-templates/', academyleadsviews.WhatsappTemplatesView.as_view(), name='whatsapp-templates'),
    path('configuration/lead-configuration/', academyleadsviews.LeadConfigurationView.as_view(), name='lead-configuration'),
    

    
    path('mark-done/', academyleadshtmx.mark_done, name='mark-done' ),
    
    path('new-leads-column/', academyleadshtmx.new_leads_column, name='new-leads-column' ),
    path('new-call/', academyleadshtmx.new_call, name='new-call' ),
    path('new-call/<int:lead_pk>/<int:call_count>/<int:max_call_count>/', academyleadshtmx.new_call, name='new-call' ),
    path('delete-lead/', academyleadshtmx.delete_lead, name='delete-lead' ),
    
    path('get-leads-column-meta-data/', academyleadshtmx.get_leads_column_meta_data, name='get-leads-column-meta-data' ),
    path('create-academy-lead/', academyleadshtmx.create_academy_lead, name='create-academy-lead' ),
    path('log-communication/', academyleadshtmx.log_communication, name='log-communication' ),
    path('add-booking/', academyleadshtmx.add_booking, name='add-booking' ),
    path('mark-arrived/', academyleadshtmx.mark_arrived, name='mark-arrived' ),
    path('mark-sold/', academyleadshtmx.mark_sold, name='mark-sold' ),
    # path('test-whatsapp-message/', academyleadshtmx.test_whatsapp_message, name='test-whatsapp-message' ),
    path('template-editor/', academyleadshtmx.template_editor, name='template-editor' ),
    path('template-save/', academyleadshtmx.template_save, name='template-save' ),
    
    path('academy-lead-get-modal-content/', academyleadshtmx.get_modal_content, name='academy-lead-get-modal-content' ),
    path('academy-lead-get-modal-content/<str:param1>/', academyleadshtmx.get_modal_content, name='academy-lead-get-modal-content' ),
    path('academy-lead-get-modal-content/<str:param1>/<str:param2>/', academyleadshtmx.get_modal_content, name='academy-lead-get-modal-content' ),
    
]
