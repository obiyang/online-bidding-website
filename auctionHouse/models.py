from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import random




class Category(models.Model):
    name = models.CharField(
        max_length=100,
        choices=[('Women','Women'),('Men','Men'),('Kids','Kids'),
                 ('Top','Top'),('Pants','Pants'),('Dresses','Dresses'),
                 ('Hoodies','Hoodies'),('Accessories','Accessories'),('Other','Other')])
    def __str__(self):
        return self.name


class Auction(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='auction_images', null=True)
    categories = models.ManyToManyField(Category)
    status = models.CharField(
        max_length=30,
        choices=[
            ('Active', 'Active'), ('Completed', 'Completed'), 
            ('Cancelled', 'Cancelled'),('Pending', 'Pending'),
            ('Failed', 'Failed')
            ],
        default='Pending'
    )
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='selling_auction')
    start_date = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField()
    reserve_price = models.DecimalField(max_digits=8, decimal_places=2)
    highest_bid = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    winner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='won_auction')
    def check_status(self):
        if self.status == 'Active' and self.end_time <= timezone.now():
            if self.highest_bid and self.highest_bid >= self.reserve_price:
                self.status = 'Completed'
            else:
                self.status = 'Failed'
            self.save()
        elif self.status == 'Pending' and self.end_time <= timezone.now():
            self.status = 'Cancelled'
            self.save()

    def save(self, *args, **kwargs):
        if self.pk and not hasattr(self, 'status_was'):
            old_instance = Auction.objects.get(pk=self.pk)
            self.status_was = old_instance.status
        super().save(*args, **kwargs)

class Bid(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bids')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user} bid on {self.auction.name} for {self.amount} on {self.time}"
    
    def clean(self):
        current_highest_bid = self.auction.bids.order_by('-amount').first()
        if current_highest_bid and self.amount <= current_highest_bid.amount:
            raise ValidationError("Bid must be higher than the current highest bid.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_messages', on_delete=models.CASCADE)
    auction = models.ForeignKey('Auction', on_delete=models.CASCADE) 
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver}"



class Rating(models.Model):
    rated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='given_ratings')
    rated_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_ratings')
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)]) 
    comment = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.rated_by} rates {self.rated_user} {self.rating}/5"

class Payment(models.Model):
    METHOD_CHOICES = [
        ('Personal Check', 'Personal Check'),
        ('Credit/Debit Card', 'Credit/Debit Card'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    ]

    auction = models.ForeignKey('Auction', on_delete=models.CASCADE, related_name='payments')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    def __str__(self):
        return f"Payment for {self.auction.name} is {self.status}"

class Shipping(models.Model):
    SHIPPING_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Shipped', 'Shipped'),
        ('In Transit', 'In Transit'),
        ('Delivered', 'Delivered'),
        ('Returned', 'Returned'),
    ]

    auction = models.ForeignKey('Auction', on_delete=models.CASCADE, related_name='shippings')
    shipping_status = models.CharField(max_length=15, choices=SHIPPING_STATUS_CHOICES)
    ups_tracking_number = models.CharField(max_length=25, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.ups_tracking_number:
            self.ups_tracking_number = ''.join([str(random.randint(0, 9)) for _ in range(25)])
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Shipping for {self.auction.name} is {self.shipping_status}"


