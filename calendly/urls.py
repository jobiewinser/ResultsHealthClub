from django.urls import path
import calendly.views as calendlyviews
urlpatterns = [
    path('calendly-webhooks/<str:guid>/', calendlyviews.Webhooks.as_view(), name='calendly-webhooks' ),
    path('calendly-booking-success/', calendlyviews.calendly_booking_success, name='calendly-booking-success' ),
    
]