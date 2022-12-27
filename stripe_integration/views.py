from core.models import Site
from core.user_permission_functions import *
import os
import stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
from django.shortcuts import redirect

def create_customer_portal_session(request):
    site_pk = request.GET.get('site_pk')
    site = Site.objects.get(pk=site_pk)
    
    if get_profile_allowed_to_change_subscription(request.user.profile, site):
        # Authenticate your user.
        session = stripe.billing_portal.Session.create(
            customer=f'{site.stripecustomer.customer_id}',
            return_url=f'{os.getenv("SITE_URL")}/configuration/site-configuration/',
        )
        return redirect(session.url)