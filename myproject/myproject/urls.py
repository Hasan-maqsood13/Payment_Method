"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from myapp import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', views.signup, name="signup"),
    path('signin/', views.signin, name="signin"),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout, name='logout'),

    path('basicdashboard/', views.basicdashboard, name='basicdashboard'),
    path('standarddashboard/', views.standarddashboard, name='standarddashboard'),
    path('premiumdashboard/', views.premiumdashboard, name='premiumdashboard'),

    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('success/', views.success, name='success'),
    path('cancel-subscription/', views.cancel_subscription, name='cancel_subscription'),


]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)