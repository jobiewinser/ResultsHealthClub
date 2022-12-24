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

# Create a function to retrieve all existing subscription links
def list_payment_methods(customer_id):
    payment_methods = stripe.PaymentMethod.list(
        customer=customer_id,
        type="card"
    )
    return payment_methods


def add_payment_method(number, exp_month, exp_year, cvc):
    try:
        # Create a PaymentMethod object
        payment_method = stripe.PaymentMethod.create(
            type='card',
            card={
                'number': number,
                'exp_month': exp_month,
                'exp_year': exp_year,
                'cvc': cvc
            },
        )
        return payment_method, None
    except Exception as e:
        return None, e.user_message  

def detach_payment_method(payment_method_id):
    try:
        # Create a PaymentMethod object
        payment_method = stripe.PaymentMethod.detach(
            payment_method=payment_method_id
        )
        return payment_method, None
    except Exception as e:
        return None, e.user_message  


def attach_payment_method(customer_id, payment_method_id):
    # Create a PaymentMethod object
    payment_method = stripe.PaymentMethod.attach(
        customer=customer_id,
        payment_method=payment_method_id,
    )
    return payment_method


# Create a function to cancel an existing subscription link
def cancel_subscription_link():
    # Cancel the subscription link
    subscription_link = stripe.billing_portal.Session.cancel(os.getenv("STRIPE_SECRET_KEY"))

    # Return the link
    return subscription_link

# List webhooks
def list_webhooks():
    return stripe.WebhookEndpoint.list(
    )

# Create webhooks
def create_webhook():
    webhook = stripe.WebhookEndpoint.create(
        url=f"{os.getenv('SITE_URL')}/stripe-webhooks/",
        enabled_events=['customer.subscription.deleted', 'customer.subscription.updated', 'customer.subscription.created'],
        api_version='2019-03-14',
        # endpoint_secret=os.getenv("STRIPE_SECRET_KEY")
    )
    return webhook

# Create webhooks
def delete_webhook(webhook_id):
    webhook = stripe.WebhookEndpoint.delete(
        sid=webhook_id,
        # endpoint_secret=os.getenv("STRIPE_SECRET_KEY")
    )
    return webhook

# # Create webhooks
# def update_subscription(subscription_id):
#     webhook = stripe.Subscription.update(
#         subscription=
#     )
#     return webhook

def create_checkout_session(checkout_session_id, price_id, customer_id):
    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            success_url=f'{str(os.getenv("SITE_URL"))}/configuration/payments-and-billing/?session_id={checkout_session_id}',
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
    
def delete_subscriptions(customer_id):
    subscriptions = list_subscriptions(customer_id)
    for subscription in subscriptions:
        subscription = stripe.Subscription.delete(
            sid=subscription['id']
        )
    return

    
def add_or_update_subscription(customer_id, payment_method, price_id):
    # Check if a subscription exists for the customer
    # customer = stripe.Customer.retrieve(customer_id)
    subscriptions = list_subscriptions(customer_id)
    # If a subscription exists, update it
    if subscriptions:
        existing_subscription = subscriptions['data'][-1]
        subscription_id = existing_subscription['id']
        if existing_subscription['plan'].stripe_id == price_id:
            return existing_subscription
        subscription = stripe.Subscription.modify(
            sid = subscription_id,
            cancel_at_period_end=False,
            proration_behavior='create_prorations',
            default_payment_method = payment_method,
            items=[{
                # 'payment_method': payment_method,
                'price': price_id,
            }],
        )
        return subscription
    # Otherwise create a new subscription
    else:
        subscription = stripe.Subscription.create(
            customer=customer_id,
            default_payment_method = payment_method,
            items=[{
                # 'payment_method': payment_method,
                'price': price_id,
            }]
        )
        return subscription
    