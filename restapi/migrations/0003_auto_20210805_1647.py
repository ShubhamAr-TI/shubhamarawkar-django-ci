# Generated by Django 3.1.6 on 2021-08-05 16:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('restapi', '0002_auto_20210805_1641'),
    ]

    operations = [
        migrations.RenameField(
            model_name='group',
            old_name='owner',
            new_name='users',
        ),
    ]
