# Generated by Django 4.2.6 on 2023-11-07 23:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Auction",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Active", "Active"),
                            ("Completed", "Completed"),
                            ("Cancelled", "Cancelled"),
                        ],
                        max_length=30,
                    ),
                ),
                ("start_date", models.DateField(auto_now_add=True)),
                ("end_time", models.DateTimeField()),
                ("reserve_price", models.DecimalField(decimal_places=2, max_digits=8)),
                ("highest_bid", models.DecimalField(decimal_places=2, max_digits=8)),
            ],
        ),
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="AuctionImage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("image", models.ImageField(upload_to="auctionHouse/images")),
                (
                    "auction",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="auctionHouse.auction",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="auction",
            name="categories",
            field=models.ManyToManyField(to="auctionHouse.category"),
        ),
        migrations.AddField(
            model_name="auction",
            name="seller",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="selling_auction",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="auction",
            name="winner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="won_auction",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
