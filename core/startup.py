
from django.conf import settings
from core.models import *
from whatsapp.models import *
from campaign_leads.models import *
from active_campaign.models import *
from messaging.models import *

def run_debug_startup():
    try:
        if settings.DEBUG:
            from django.contrib.auth.models import User
            user, created = User.objects.get_or_create(
                username="jobie",
                defaults={
                    'first_name': "jobie",
                    'last_name': "winser",
                }
            )
            user.set_password(os.getenv("DEFAULT_USER_PASSWORD"))
            user.save()
            
            company, created = Company.objects.get_or_create(
                name="Test Company",
                defaults={
                    'active_campaign_url': os.getenv("DEFAULT_ACTIVE_CAMPAIGN_URL"),
                    'active_campaign_api_key': os.getenv("DEFAULT_ACTIVE_CAMPAIGN_API_KEY"),
                }
            )

            site, created = Site.objects.get_or_create(
                name="Test Site",
                defaults={
                    'company': company,
                    'whatsapp_access_token': os.getenv("DEFAULT_WHATSAPP_ACCESS_TOKEN"),
                    'whatsapp_app_secret_key': os.getenv("DEFAULT_WHATSAPP_SECRET_KEY"),
                    'calendly_token': os.getenv("DEFAULT_CALENDLY_TOKEN"),
                    'calendly_organization': os.getenv("DEFAULT_CALENDLY_ORGANIZATION"),
                    'guid': "6325bcde-feb9-4c",
                }
            )

            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults={
                    'company': company,
                    'site': site,
                }      
            )
    except:
        pass