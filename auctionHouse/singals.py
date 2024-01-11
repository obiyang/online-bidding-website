from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Auction, Message
from django.contrib.auth.models import User




@receiver(pre_save, sender=Auction)
def update_auction_status(sender, instance, **kwargs):
    instance.check_status()
    if instance.status in ['Completed', 'Cancelled'] and instance.status_was == 'Active':
        instance.end_time = timezone.now()

@receiver(post_save, sender=Auction)
def send_message_to_winner(sender, instance, created, **kwargs):
    if instance.status == 'Completed' and instance.winner:
        
        admin_user = User.objects.filter(is_superuser=True).first()
        
        
        message = Message.objects.create(
            sender=admin_user,
            receiver=instance.winner,
            content=f"Congratulations! You have won the auction for '{instance.name}'.Message me to schedule a date to bring the personal check, and I will send you the tracking number for your item",
            auction=instance
        )

@receiver(post_save, sender=Auction)
def send_message_to_seller(sender, instance, created, **kwargs):
    if instance.status == 'Completed' and instance.winner:
        
        admin_user = User.objects.filter(is_superuser=True).first()
        
        
        message = Message.objects.create(
            sender=admin_user,
            receiver=instance.seller,
            content=f"Congratulations! Your auction '{instance.name}' has a winner .Message me to get more info!",
            auction=instance
        )