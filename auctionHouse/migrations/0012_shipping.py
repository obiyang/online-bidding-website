# Generated by Django 4.2.6 on 2023-11-30 02:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auctionHouse', '0011_payment'),
    ]

    operations = [
        migrations.CreateModel(
            name='Shipping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shipping_status', models.CharField(choices=[('Pending', 'Pending'), ('Shipped', 'Shipped'), ('In Transit', 'In Transit'), ('Delivered', 'Delivered'), ('Returned', 'Returned')], max_length=15)),
                ('auction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shippings', to='auctionHouse.auction')),
            ],
        ),
    ]
