# Generated by Django 3.1.6 on 2021-08-05 17:57

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('restapi', '0005_auto_20210805_1756'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expense',
            name='users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
    ]
