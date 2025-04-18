# Generated by Django 5.1.5 on 2025-04-07 06:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0003_product_type"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="product",
            name="type",
        ),
        migrations.AddField(
            model_name="product",
            name="product_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("broiler", "Broiler"),
                    ("layer", "Layers"),
                    ("kienyeji", "Kienyeji"),
                    ("feeds", "Feeds"),
                ],
                max_length=100,
                null=True,
            ),
        ),
    ]
