# Generated by Django 3.1.6 on 2021-08-16 18:56

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('restapi', '0002_auto_20210814_1325'),
    ]

    operations = [
        migrations.CreateModel(
            name='Counter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('counter_type',
                 models.CharField(choices=[('PROCESS_ID', 'process_id'), ('PROCESS_ID2', 'process_id2')],
                                  max_length=1000)),
                ('counter', models.SmallIntegerField(default=0)),
            ],
        ),
    ]
