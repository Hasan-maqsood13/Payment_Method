from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from myapp.models import *
import stripe
from django.conf import settings
import os
import django
import sys

# Set the path to your Django project root where manage.py is located
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')  # <-- Replace with your actual project name
django.setup()

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

class Command(BaseCommand):
    help = 'Checks and updates expired subscriptions'

    def handle(self, *args, **options):
        now = timezone.now()
        active_subs = Subscription.objects.filter(status='active')
        
        for sub in active_subs:
            if sub.end_date <= now:
                try:
                    # Update Stripe
                    stripe.Subscription.modify(
                        sub.stripe_subscription_id,
                        cancel_at_period_end=True
                    )
                    
                    # Update our database
                    sub.status = 'expire'
                    sub.save()
                    
                    self.stdout.write(f"Expired subscription for {sub.user.username}")
                except stripe.error.StripeError as e:
                    self.stdout.write(f"Error updating subscription {sub.id}: {str(e)}")