import stripe
import os
from django.views.decorators.csrf import csrf_exempt
from core.models import Site, SiteSubscriptionChange
# Set your secret key. Remember to switch to your live secret key in production.
# See your keys here: https://dashboard.stripe.com/apikeys
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

from django.http import HttpResponse
from datetime import datetime
# If you are testing your webhook locally with the Stripe CLI you
# can find the endpoint's secret by running `stripe listen`
# Otherwise, find your endpoint's secret in your webhook settings in the Developer Dashboard
endpoint_secret = os.getenv('STRIPE_SIGNING_SECRET')

# Using Django
@csrf_exempt
def webhooks(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

  # Handle the event
    site =  Site.objects.filter(stripecustomer__customer_id=event['data']['object']['customer']).first()
    if event['type'] == 'customer.subscription.created':
        if site:
            site.get_stripe_subscriptions_and_update_models
            site_subscription_change = SiteSubscriptionChange.objects.filter(site=site, completed=datetime.now()).last()
            if site_subscription_change:
                site_subscription_change.process()
        print()
    elif event['type'] == 'customer.subscription.deleted':
        if site:
            site.get_stripe_subscriptions_and_update_models
            site_subscription_change = SiteSubscriptionChange.objects.filter(site=site, completed=datetime.now()).last()
            if site_subscription_change:
                site_subscription_change.process()
        print()
    elif event['type'] == 'customer.subscription.updated':
        if site:
            site.get_stripe_subscriptions_and_update_models
            site_subscription_change = SiteSubscriptionChange.objects.filter(site=site, completed=datetime.now()).last()
            if site_subscription_change:
                site_subscription_change.process()
        print()
    # ... handle other event types
    else:
        print('Unhandled event type {}'.format(event['type']))

    return HttpResponse(status=200)