import os
import django

# Set up Django environment - yahan 'your_project_name' ko apne project ke naam se replace karein
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.conf import settings
import stripe

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

def create_stripe_products_and_prices():
    plans = {
        "basic": {"amount": 500, "interval": "day", "interval_count": 10},
        "standard": {"amount": 1500, "interval": "day", "interval_count": 20},
        "premium": {"amount": 3000, "interval": "day", "interval_count": 30},
    }

    created_data = {}

    for plan_name, data in plans.items():
        # Create product
        product = stripe.Product.create(name=f"{plan_name.capitalize()} Plan")

        # Create price with recurring billing interval
        price = stripe.Price.create(
            unit_amount=data["amount"],
            currency="usd",
            recurring={
                "interval": data["interval"],
                "interval_count": data["interval_count"],
            },
            product=product.id,
        )

        print(f"Created {plan_name} plan:")
        print(f" Product ID: {product.id}")
        print(f" Price ID: {price.id}\n")

        created_data[plan_name] = {
            "product_id": product.id,
            "price_id": price.id
        }

    print("All plans created successfully!")
    print("Save these Price IDs for your application:")
    print(created_data)

if __name__ == "__main__":
    create_stripe_products_and_prices()
