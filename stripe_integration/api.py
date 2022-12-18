import stripe
import os
# Set your secret key: remember to change this to your live secret key in production
# See your keys here: https://dashboard.stripe.com/account/apikeys
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

import stripe

# Create a Subscription
def createSubscription(customer, plan):
    subscription = stripe.Subscription.create(
        customer=customer,
        items=[
            {
                'plan': plan,
            },
        ]
    )
    return subscription

# List existing Subscriptions
def listSubscriptions():
    subscriptions = stripe.Subscription.list()
    return subscriptions

# Create webhooks
def createWebhooks(endpoint_secret):
    webhook = stripe.WebhookEndpoint.create(
        url=f"{os.getenv('SITE_URL')}/webhook",
        enabled_events=['customer.subscription.deleted', 'customer.subscription.deleted', 'customer.subscription.deleted'],
        api_version='2019-03-14',
        endpoint_secret=endpoint_secret
    )
    return webhook