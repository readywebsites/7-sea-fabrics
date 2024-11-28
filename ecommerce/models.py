from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django_countries.fields import CountryField


# Create your models here.

class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=100)
    conversion_rate = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.code
    

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    additional_addresses = models.TextField(blank=True, null=True)  # Can store multiple addresses in JSON format

    def __str__(self):
        return self.user.username

    def add_address(self, address):
        if self.additional_addresses is None:
            self.additional_addresses = []
        self.additional_addresses.append(address)
        self.save()

    def remove_address(self, address_index):
        if self.additional_addresses:
            try:
                del self.additional_addresses[address_index]
                self.save()
            except IndexError:
                pass
                
# Signal to create or update user profile
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created and not instance.is_superuser:
        UserProfile.objects.create(user=instance)
    if not instance.is_superuser:
        instance.userprofile.save()

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2) #price USD
    old_price = models.DecimalField(max_digits=10, decimal_places=2,blank=True,null=True)
    stock = models.IntegerField()
    image = models.ImageField(upload_to='products/')

    def __str__(self):
        return self.name
    

    def get_price(self, currency):
        if currency == 'USD':
            return self.price
        else:
            # Convert price to the selected currency using the conversion rate
            try:
                target_currency = Currency.objects.get(code=currency)
                converted_price = self.price * Decimal(target_currency.conversion_rate)
                return converted_price.quantize(Decimal('0.01'))  # Format to 2 decimal places
            except Currency.DoesNotExist:
                return None

class Cart(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=40, null=True, blank=True)
    products = models.ManyToManyField(Product, through='CartProduct')

    def __str__(self):
        if self.user:
            return f"Cart of {self.user.username}"
        return f"Cart with session {self.session_id}"

    def get_total_price(self):
        total = sum(item.product.price * item.quantity for item in self.cartproduct_set.all())
        return total

    def count_unique_items(self):
        unique_items_count = self.cartproduct_set.count()  # Count all CartProduct instances
        return unique_items_count
    

class CartProduct(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.product.name} in {self.cart}"
    


class Wishlist(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=40, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'session_id', 'product')

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    address_line_1 = models.CharField(max_length=255)
    country = CountryField()
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)  # New field for phone number

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.address_line_1},{self.country},{self.state},{self.city},{self.zipcode},{self.phone}"


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through='OrderProduct')
    shipping_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ])
    payment_status = models.CharField(max_length=20, choices=[
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ], default='unpaid')

    def __str__(self):
        return f"Order #{self.pk} by {self.user.username}"

    def get_total_price(self):
        total = sum(op.product.price * op.quantity for op in self.orderproduct_set.all())
        return total
    
    def get_invoice_number(self):
        return f"SM{self.pk:05d}"
    
    def formatted_created_at(self):
        return self.created_at.strftime('%d.%m.%Y')

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} of {self.product.name} in order {self.order.id}"
