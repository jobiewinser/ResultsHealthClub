
from django.conf import settings
from core.models import *
from whatsapp.models import *
from campaign_leads.models import *
from active_campaign.models import *
from messaging.models import *
from django.contrib.auth.models import Group
from datetime import datetime
import sys
def run_debug_startup():
    if not sys.argv[1] in ["makemigrations", "migrate", "collectstatic", "random_leads"]:
        if settings.DEBUG:
            from django.contrib.auth.models import User
            user, created = User.objects.get_or_create(
                username="vagrant",
            )
            user.first_name = "vagrant"
            user.last_name = "vagrant"
            user.is_superuser = True
            user.is_staff = True
            user.save()
            
            user.set_password(os.getenv("DEFAULT_USER_PASSWORD"))
            
            company, created = Company.objects.get_or_create(
                name="Test Company",
            )
            company.active_campaign_url = os.getenv("DEFAULT_ACTIVE_CAMPAIGN_URL")
            company.active_campaign_api_key = os.getenv("DEFAULT_ACTIVE_CAMPAIGN_API_KEY")
            company.subscription = 'pro'
            company.save()

            site, created = Site.objects.get_or_create(
                name="Test Site",
                company=company,
            )
            site.whatsapp_access_token = os.getenv("default_whatsapp_access_token")
            site.calendly_token = os.getenv("DEFAULT_CALENDLY_TOKEN")
            site.calendly_organization = os.getenv("DEFAULT_CALENDLY_ORGANIZATION")
            site.guid = "6325bcde-feb9-4c"
            site.save()

            whatsapp_business_account, created = WhatsappBusinessAccount.objects.get_or_create(
                site = site,
                whatsapp_business_account_id="100707722886543",
            )
            whatsapp_template_1, created = WhatsappTemplate.objects.get_or_create(
                whatsapp_business_account = whatsapp_business_account,    
                company = company,
                name = "hello_world"
            )
            whatsapp_template_1.name = "hello_world"
            whatsapp_template_1.edited = datetime.now()
            whatsapp_template_1.status = "APPROVED"
            whatsapp_template_1.message_template_id = "505825570915381"
            whatsapp_template_1.category = "ACCOUNT_UPDATE"
            whatsapp_template_1.language = "en_US"
            whatsapp_template_1.last_approval = datetime.now()
            whatsapp_template_1.components = [
                    {"text": "Hello World", "type": "HEADER", "format": "TEXT"},
                    {"text": "Welcome and congratulations!! This message demonstrates your ability to send a message notification from WhatsApp Business Platform’s Cloud API. Thank you for taking the time to test with us.", "type": "BODY"},
                    {"text": "WhatsApp Business API Team", "type": "FOOTER"}
                ]
            whatsapp_template_1.save()
            
            whatsapp_number1, created = WhatsappNumber.objects.get_or_create(
                company=company,
                whatsapp_business_account = whatsapp_business_account,
            )
            whatsapp_number1.quality_rating = "UNKNOWN"
            whatsapp_number1.whatsapp_business_phone_number_id = "104174565866954"
            whatsapp_number1.code_verification_status = "DEMO MODE"
            whatsapp_number1.verified_name = "Live Phone"
            whatsapp_number1.number = "447807041680"
            whatsapp_number1.alias = "Live Phone"
            whatsapp_number1.save()

            profile, created = Profile.objects.get_or_create(
                user=user
            )            
            profile.calendly_event_page_url = "https://calendly.com/winsersystems"
            profile.company = company
            profile.site = site
            profile.role = 'a'            
            profile.save()
            profile.sites_allowed.set([site])

            siteprofilepermissions = profile.siteprofilepermissions_set.filter(site=site).first()
            if siteprofilepermissions:
                for field in siteprofilepermissions._meta.fields:
                    if type(field) == models.BooleanField:
                        setattr(siteprofilepermissions, field.attname, True)
                siteprofilepermissions.save()
animals = [
            ('cat','0, 0, 255','blue'),
            ('cow','255, 0, 0','red'),
            ('crow','0, 255, 0','green'),
            ('dog','255, 128, 128','pink'),
            ('dove','255, 0, 255','magenta'),
            ('dragon','255, 128, 128','pink'),
            ('fish','128, 128, 128','grey'),
            ('frog','128, 0, 0','brown'),
            ('hippo','255, 128, 0','orange'),
            ('horse','0, 0, 255','blue'),
            ('kiwi-bird','255, 0, 0','red'),
            ('locust','0, 255, 0','green'),
            ('mosquito','255, 128, 128','pink'),
            ('otter','255, 0, 255','magenta'),
            ('shrimp','255, 128, 128','pink'),
            ('spider','128, 128, 128','grey'),
            ('worm', '255, 128, 0','brown')
        ]
        
def run_startup():
    try:
        if not sys.argv[1] in ["makemigrations", "migrate", "collectstatic", "random_leads"]:
            SiteUsersOnline.objects.all().update(users_online="")
    except:
        pass
def run_demo_startup():
    if settings.DEMO:
        #TODO change the line below to only run for runserver, runserver_plus and whatever gunicorn runs
        if not sys.argv[1] in ["makemigrations", "migrate", "collectstatic", "random_leads"]:
            group, created = Group.objects.get_or_create(
                name="demo"
            )
        
            company, created = Company.objects.get_or_create(
                name="Demo Company",
                demo=True,
            )   
            company.subscription = 'pro'
            company.save()
            site1, created = Site.objects.get_or_create(
                name="Abingdon Site",
                company=company,
            )
            site1.calendly_token = os.getenv("DEFAULT_CALENDLY_TOKEN")
            site1.calendly_organization = os.getenv("DEFAULT_CALENDLY_ORGANIZATION")
            site1.save()
            
            campaign_category1, created = CampaignCategory.objects.get_or_create(
                name="Fitness Academies",
                site=site1
            )
            campaign_category2, created = CampaignCategory.objects.get_or_create(
                name="PT Training Courses",
                site=site1
            )
            whatsapp_business_account1, created = WhatsappBusinessAccount.objects.get_or_create(
                site = site1,
                whatsapp_business_account_id="1",
            )
            whatsapp_number1, created = WhatsappNumber.objects.get_or_create(
                company=company,
                whatsapp_business_account = whatsapp_business_account1,
            )
            whatsapp_number1.quality_rating = "UNKNOWN"
            whatsapp_number1.whatsapp_business_phone_number_id = "1"
            whatsapp_number1.code_verification_status = "DEMO MODE"
            whatsapp_number1.verified_name = "Demo Phone"
            whatsapp_number1.number = "07872123456"
            whatsapp_number1.alias = "Demo Phone"
            whatsapp_number1.save()
            whatsapp_template_1, created = WhatsappTemplate.objects.get_or_create(
                whatsapp_business_account = whatsapp_business_account1,    
                company = company,
            )
            whatsapp_template_1.name = "demo_whatsapp_template"
            whatsapp_template_1.edited = datetime.now()
            whatsapp_template_1.status = "APPROVED"
            whatsapp_template_1.message_template_id = "1"
            whatsapp_template_1.category = "ACCOUNT_UPDATE"
            whatsapp_template_1.language = "en_US"
            whatsapp_template_1.last_approval = datetime.now()
            whatsapp_template_1.components = [
                    {
                        "text": "Hi [[1]]",
                        "type": "HEADER",
                        "format": "TEXT"
                    },
                    {
                        "text": "This is a demonstration of the whatsapp system! With the Pro subscription, you can add your own whatsapp accounts and automate sending templates here!",
                        "type": "BODY"
                    },
                    {
                        "text": "Thanks from Winser Systems!",
                        "type": "FOOTER"
                    }
                ]
            whatsapp_template_1.save()

            campaign1, created = Campaign.objects.get_or_create(
                name="Group Strength Training",
                campaign_category=campaign_category1,
                site=site1,
                company=company,
                whatsapp_business_account=whatsapp_business_account1,
            )

            campaign2, created = Campaign.objects.get_or_create(
                name="Group Cardio Training",
                campaign_category=campaign_category1,
                site=site1,
                company=company,
                whatsapp_business_account=whatsapp_business_account1,
            )

            campaign3, created = Campaign.objects.get_or_create(
                name="Individual PT Training",
                campaign_category=campaign_category2,
                site=site1,
                company=company,
                whatsapp_business_account=whatsapp_business_account1,
            )
            for animal in animals:                
                user, created = User.objects.get_or_create(
                    username=f"{animal[2]}{animal[0]}",
                )
                user.first_name=animal[2].capitalize()
                user.last_name=f"{animal[0].capitalize()} (Demo User)"
                user.set_password(os.getenv("DEFAULT_USER_PASSWORD"))
                user.save()
                group.user_set.add(user)
                profile, created = Profile.objects.get_or_create(
                    user=user
                )
                # if created:
                profile.avatar = f"demo-profiles/{animal[0]}-solid.svg"
                profile.calendly_event_page_url = "https://calendly.com/winsersystems"
                profile.demo_account_theme_colour = animal[1]
                profile.company = company
                profile.site = site1
                profile.save()
                profile.sites_allowed.set([site1])