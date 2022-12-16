from django.urls import path
import calendly.views as calendlyviews
urlpatterns = [
    path('calendly-webhooks/<str:guid>/', calendlyviews.Webhooks.as_view(), name='calendly-webhooks' ),
    path('calendly-booking-success/', calendlyviews.calendly_booking_success, name='calendly-booking-success' ),
    path('get-latest-calendly-booking-info/', calendlyviews.get_latest_calendly_booking_info, name='get-latest-calendly-booking-info' ),
    
]