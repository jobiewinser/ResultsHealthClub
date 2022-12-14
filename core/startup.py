
from django.conf import settings
from core.models import *
from whatsapp.models import *
from campaign_leads.models import *
from active_campaign.models import *
from messaging.models import *
from django.contrib.auth.models import Group

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
animals = [
            'cat',
            'cow',
            'crow',
            'dog',
            'dove',
            'dragon',
            'fish',
            'frog',
            'hippo',
            'horse',
            'kiwi-bird',
            'locust',
            'mosquito',
            'otter',
            'shrimp',
            'spider',
            'worm'
        ]
def run_demo_startup():
    if settings.DEMO:
        for index in ['one', 'two']:
            for animal in animals:
                group, created = Group.objects.get_or_create(
                    name="demo"
                )
            
                company, created = Company.objects.get_or_create(
                    name="Demo Company",
                )   

                site1, created = Site.objects.get_or_create(
                    name="Abingdon Site",
                    company=company,
                    defaults={
                        'calendly_token': os.getenv("DEFAULT_CALENDLY_TOKEN"),
                        'calendly_organization': os.getenv("DEFAULT_CALENDLY_ORGANIZATION"),
                    }
                )

                # site2, created = Site.objects.get_or_create(
                #     name="Paignton Site",
                #     company=company,
                #     defaults={
                #         'calendly_token': os.getenv("DEFAULT_CALENDLY_TOKEN"),
                #         'calendly_organization': os.getenv("DEFAULT_CALENDLY_ORGANIZATION"),
                #     }
                # )
                campaign_category1, created = CampaignCategory.objects.get_or_create(
                    name="Fitness Academies",
                    site=site1
                )
                campaign_category2, created = CampaignCategory.objects.get_or_create(
                    name="PT Training Courses",
                    site=site1
                )

                campaign1, created = Campaign.objects.get_or_create(
                    name="Group Strength Training",
                    campaign_category=campaign_category1,
                    site=site1,
                    company=company,
                )

                campaign2, created = Campaign.objects.get_or_create(
                    name="Group Cardio Training",
                    campaign_category=campaign_category1,
                    site=site1,
                    company=company,
                )

                campaign3, created = Campaign.objects.get_or_create(
                    name="Individual PT Training",
                    campaign_category=campaign_category2,
                    site=site1,
                    company=company,
                )
                user, created = User.objects.get_or_create(
                    username=f"{animal}{index}",
                )
                if created:
                    user.first_name=animal.capitalize()
                    user.last_name=index.capitalize()
                    user.set_password(os.getenv("DEFAULT_USER_PASSWORD"))
                    user.save()
                group.user_set.add(user)
                profile, created = Profile.objects.get_or_create(
                    user=user
                )
                if created:
                    profile.avatar = "demo-profiles/{animal}-solid.svg"
                    profile.company = company
                    profile.site = site1
                    profile.save()