# Generated by Django 3.0.4 on 2020-03-25 09:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wx_client', '0007_auto_20200325_1751'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='u_uuid',
            field=models.UUIDField(unique=True),
        ),
    ]
