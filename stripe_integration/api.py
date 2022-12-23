import stripe
import os
# Set your secret key: remember to change this to your live secret key in production
# See your keys here: https://dashboard.stripe.com/account/apikeys
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
from django.shortcuts import redirect
import stripe

# Create a Subscription
def create_subscription(customer_id, price_ids):
    prices = []
    for price_id in price_ids:
        prices.append(
            {
                'price': price_id,
            },
        )
    subscription = stripe.Subscription.create(
        customer=customer_id,
        items=prices
    )
    return subscription
    
# Create a function to retrieve an existing subscription link
def get_or_create_customer(customer_id=""):
    try:
        customer = stripe.Customer.retrieve(customer_id)
    except stripe.error.InvalidRequestError:
        customer = stripe.Customer.create()
    return customer
    
# Create a function to retrieve an existing subscription link
def retrieve_subscription_link(session_id):
    # Retrieve the link
    subscription_link = stripe.billing_portal.Session.retrieve(session_id)

    # Return the link
    return subscription_link

# Create a function to retrieve all existing subscription links
def list_subscriptions(customer_id):
    # subscriptions = stripe.Subscription.list({
    #     'customer':customer_id,
    # })
    subscriptions = stripe.Subscription.list(
        customer=customer_id
    )
    return subscriptions

# Create a function to cancel an existing subscription link
def cancel_subscription_link(session_id):
    # Cancel the subscription link
    subscription_link = stripe.billing_portal.Session.cancel(session_id)

    # Return the link
    return subscription_link

# Create webhooks
def create_webhooks(endpoint_secret):
    webhook = stripe.WebhookEndpoint.create(
        url=f"{os.getenv('SITE_URL')}/webhook",
        enabled_events=['customer.subscription.deleted', 'customer.subscription.deleted', 'customer.subscription.deleted', 'customer.subscription.deleted'],
        api_version='2019-03-14',
        endpoint_secret=endpoint_secret
    )
    return webhook

def create_checkout_session(checkout_session_id, price_id, customer_id):
    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            success_url=f'{str(os.getenv("SITE_URL"))}/stripe-subscription-summary/?session_id={checkout_session_id}',
            cancel_url=f'{str(os.getenv("SITE_URL"))}/stripe-subscription-canceled/',
            mode='subscription',
            line_items=[{
                'price': price_id,
                # For metered billing, do not pass quantity
                'quantity': 1
            }],
        )

    except Exception as e:
        return str(e)

    return session