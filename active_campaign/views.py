from datetime import datetime
import logging
from django.http import HttpResponse
import json
from django.views.decorators.csrf import csrf_exempt
from academy_leads.models import AcademyLead, Communication

from whatsapp.models import WhatsAppMessage, WhatsAppMessageStatus
logger = logging.getLogger(__name__)
from django.views import View 
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name="dispatch")
class Webhooks(View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse("")
        response.status_code = 200
        return response

    def post(self, request, *args, **kwargs):                        
        response = HttpResponse("")
        response.status_code = 200     
        
        return response