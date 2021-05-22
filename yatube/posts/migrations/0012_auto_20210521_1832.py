# Generated by Django 2.2.6 on 2021-05-21 18:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0011_follow'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('user', 'author'), name='unique_object'),
        ),
    ]