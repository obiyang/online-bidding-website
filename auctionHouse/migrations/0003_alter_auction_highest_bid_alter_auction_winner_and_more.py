# Generated by Django 4.2.6 on 2023-11-22 23:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("auctionHouse", "0002_auction_image_delete_auctionimage"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auction",
            name="highest_bid",
            field=models.DecimalField(decimal_places=2, max_digits=8, null=True),
        ),
        migrations.AlterField(
            model_name="auction",
            name="winner",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="won_auction",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="category",
            name="name",
            field=models.CharField(
                choices=[
                    ("Women", "Women"),
                    ("Men", "Men"),
                    ("Kids", "Kids"),
                    ("Top", "Top"),
                    ("Pants", "Pants"),
                    ("Dresses", "Dresses"),
                    ("Hoodies", "Hoodies"),
                    ("Accessories", "Accessories"),
                    ("Other", "Other"),
                ],
                max_length=100,
            ),
        ),
    ]