# Generated by Django 5.1.5 on 2025-04-03 10:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_alter_product_price_alter_product_quantity'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='type',
            field=models.CharField(default='General', max_length=100),
        ),
    ]
