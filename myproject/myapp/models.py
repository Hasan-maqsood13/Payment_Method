from django.db import models
from django.utils import timezone

class Registration(models.Model):
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    date_joined = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)

    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('customer', 'Customer'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')

    def __str__(self):
        return self.username


class Subscription(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('cancel', 'Canceled'),
        ('expire', 'Expired'),
    )

    user = models.ForeignKey(Registration, on_delete=models.CASCADE)
    plan_name = models.CharField(max_length=20, default='basic')
    stripe_subscription_id = models.CharField(max_length=100, default='')
    stripe_customer_id = models.CharField(max_length=100, default='')
    amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.plan_name} - {self.status}"
