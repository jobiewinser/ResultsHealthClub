import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
logger = logging.getLogger(__name__)
from django.views import View 
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name="dispatch")
class MessageWebhooks(View):
    def get(self, request, *args, **kwargs):
        logger.debug(f"MessageWebhooks get {str(request.GET)}")                 
        response = HttpResponse("")
        response.status_code = 200
        return response

    def post(self, request, *args, **kwargs):
        logger.debug(f"MessageWebhooks post {str(request.POST)}")                      
        response = HttpResponse("")
        response.status_code = 200             
        return response

@method_decorator(csrf_exempt, name="dispatch")
class StatusWebhooks(View):
    def get(self, request, *args, **kwargs):
        logger.debug(f"StatusWebhooks get {str(request.GET)}")            
        response = HttpResponse("")
        response.status_code = 200
        return response

    def post(self, request, *args, **kwargs):
        logger.debug(f"StatusWebhooks post {str(request.POST)}")                      
        response = HttpResponse("")
        response.status_code = 200             
        return response