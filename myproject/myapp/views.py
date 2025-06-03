from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse, HttpResponseForbidden
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from django.core.mail import send_mail
from .models import *
import random
import re
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.timezone import make_aware
from datetime import datetime
from django.core import serializers
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.utils.dateparse import parse_datetime
from django.db.models import Sum
import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.timezone import make_aware
from datetime import datetime
from django.utils import timezone
from django.views.decorators.cache import never_cache
import stripe
from django.conf import settings 
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from .models import Registration, Subscription
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages




stripe.api_key = settings.STRIPE_TEST_SECRET_KEY  

PRICE_IDS = {
    'basic': 'price_1RVpr0BI8a0PuxwiaJao2CFY',  
    'standard': 'price_1RVpr2BI8a0Puxwi3AU0DkHO',
    'premium': 'price_1RVpr3BI8a0Puxwit3ToAPew',
}

@csrf_exempt
def create_checkout_session(request):
    if request.method == 'POST':
        plan = request.POST.get('plan')
        price_id = PRICE_IDS.get(plan)
        if not price_id:
            return JsonResponse({'error': 'Invalid plan selected'}, status=400)

        user_email = request.session.get('email')
        user = Registration.objects.get(email=user_email)

        customer = stripe.Customer.create(email=user.email)

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer=customer.id,
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{request.build_absolute_uri('/success/')}?plan={plan}&customer_id={customer.id}",
            cancel_url=request.build_absolute_uri('/dashboard/'),
            
        )

        return redirect(session.url)
    return HttpResponseForbidden()


def success(request):
    plan = request.GET.get('plan')
    customer_id = request.GET.get('customer_id')

    if not plan or not customer_id:
        return HttpResponse("Missing plan or customer information", status=400)

    user_email = request.session.get('email')
    if not user_email:
        return HttpResponse("User not authenticated", status=401)

    try:
        user = Registration.objects.get(email=user_email)
    except Registration.DoesNotExist:
        return HttpResponse("User not found", status=404)

    try:
        # Get the latest subscription for this customer
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            status='all',
            limit=1
        )
        
        if not subscriptions.data:
            return HttpResponse("No subscription found", status=404)

        subscription = subscriptions.data[0]
        
        # Set default dates (now and 30 days from now)
        # start_dt = timezone.now()
        # end_dt = start_dt + timedelta(days=30)
        start_dt = timezone.now()
        end_dt = start_dt + timedelta(minutes=2)


        
        # Try to get period dates from subscription if available
        if 'current_period_start' in subscription:
            start_dt = timezone.make_aware(datetime.fromtimestamp(subscription.current_period_start))
        if 'current_period_end' in subscription:
            end_dt = timezone.make_aware(datetime.fromtimestamp(subscription.current_period_end))

        # Get the plan amount (handle different Stripe API versions)
        amount = 0
        if hasattr(subscription, 'plan') and subscription.plan:
            amount = float(subscription.plan.amount) / 100
        elif hasattr(subscription, 'items') and subscription.items.data:
            amount = float(subscription.items.data[0].price.unit_amount) / 100

        # Create the subscription record
        Subscription.objects.create(
            user=user,
            plan_name=plan,
            stripe_subscription_id=subscription.id,
            stripe_customer_id=customer_id,
            amount=amount,
            status=subscription.status,
            start_date=start_dt,
            end_date=end_dt
        )

        # Redirect to appropriate dashboard
        if plan == 'basic':
            return redirect('basicdashboard')
        elif plan == 'standard':
            return redirect('standarddashboard')
        elif plan == 'premium':
            return redirect('premiumdashboard')

    except stripe.error.StripeError as e:
        return HttpResponse(f"Stripe error: {str(e)}", status=400)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=400)

    return HttpResponse("Subscription processed successfully")

# Create your views here.
def signup(request):
    if request.method == 'POST':
        username = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = Registration(
            username=username,
            email=email,
            password=password,  # Ideally, password should be hashed
        )
        user.save()
        return redirect('signin')
    return render(request, 'signup.html')

def signin(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = Registration.objects.get(email=email)
        except Registration.DoesNotExist:
            return render(request, 'Signin.html', {'error': "User with this email does not exist."})

        if password == user.password:
            request.session['email'] = user.email

            try:
                subscription = Subscription.objects.filter(user=user).latest('start_date')

                # Check if subscription is active and not expired
                if subscription.status == 'active' and subscription.end_date > timezone.now():
                    # Redirect based on plan
                    if subscription.plan_name == 'basic':
                        return redirect('basicdashboard')
                    elif subscription.plan_name == 'standard':
                        return redirect('standarddashboard')
                    elif subscription.plan_name == 'premium':
                        return redirect('premiumdashboard')
                else:
                    # Subscription expired or canceled
                    messages.warning(request, "آپ کی سبسکرپشن ختم یا منسوخ ہو چکی ہے، براہ کرم نیا پلان منتخب کریں۔")
                    return redirect('dashboard')

            except Subscription.DoesNotExist:
                # No subscription exists
                return redirect('dashboard')
        else:
            return render(request, 'Signin.html', {'error': "Invalid password. Please try again."})

    return render(request, 'Signin.html')

@csrf_protect
def logout(request):
    if request.method == 'POST':
        request.session.flush()  # Clears all session data
        return redirect('signin')
    return redirect('dashboard')
def basicdashboard(request):
    user_email = request.session.get('email')
    user = Registration.objects.get(email=user_email)

    try:
        subscription = Subscription.objects.filter(user=user).latest('start_date')
        if subscription.plan_name != 'basic' or subscription.status != 'active':
            messages.warning(request, "Access denied. You don't have a Basic plan.")
            return redirect('dashboard')  # ya aapka main dashboard ka url name
    except Subscription.DoesNotExist:
        messages.warning(request, "No active subscription found.")
        return redirect('dashboard')

    return render(request, 'basicdashboard.html', {
        'user': user,
        'subscription': subscription
    })

def standarddashboard(request):
    user_email = request.session.get('email')
    user = Registration.objects.get(email=user_email)

    try:
        subscription = Subscription.objects.filter(user=user).latest('start_date')
        if subscription.plan_name != 'standard' or subscription.status != 'active':
            messages.warning(request, "Access denied. You don't have a Standard plan.")
            return redirect('dashboard')
    except Subscription.DoesNotExist:
        messages.warning(request, "No active subscription found.")
        return redirect('dashboard')

    return render(request, 'standarddashboard.html', {
        'user': user,
        'subscription': subscription
    })

def premiumdashboard(request):
    user_email = request.session.get('email')
    user = Registration.objects.get(email=user_email)

    try:
        subscription = Subscription.objects.filter(user=user).latest('start_date')
        if subscription.plan_name != 'premium' or subscription.status != 'active':
            messages.warning(request, "Access denied. You don't have a Premium plan.")
            return redirect('dashboard')
    except Subscription.DoesNotExist:
        messages.warning(request, "No active subscription found.")
        return redirect('dashboard')

    return render(request, 'premiumdashboard.html', {
        'user': user,
        'subscription': subscription
    })


@never_cache
def dashboard(request):
    if 'email' not in request.session:
        return redirect('signin')
    return render(request, 'dashboard.html')

@csrf_exempt
def cancel_subscription(request):
    if request.method == 'POST':
        user_email = request.session.get('email')
        if not user_email:
            return HttpResponse("User not logged in", status=401)
        
        try:
            user = Registration.objects.get(email=user_email)
            subscription = Subscription.objects.filter(user=user).latest('start_date')

            # Cancel the Stripe subscription
            stripe.Subscription.delete(subscription.stripe_subscription_id)

            # Optionally update subscription status in DB
            subscription.status = 'canceled'
            subscription.end_date = timezone.now()
            subscription.save()

            messages.success(request, "Subscription canceled successfully.")
            return redirect('dashboard')

        except Registration.DoesNotExist:
            return HttpResponse("User not found", status=404)
        except Subscription.DoesNotExist:
            return HttpResponse("Subscription not found", status=404)
        except stripe.error.StripeError as e:
            return HttpResponse(f"Stripe error: {str(e)}", status=400)
        except Exception as e:
            return HttpResponse(f"Error: {str(e)}", status=400)

    return HttpResponseForbidden()
