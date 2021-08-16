# Generated by Django 3.1.6 on 2021-08-14 13:25

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('restapi', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expense',
            name='total_amount',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='userexpense',
            name='amount_lent',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='userexpense',
            name='amount_owed',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
    ]