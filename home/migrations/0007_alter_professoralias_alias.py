# Generated by Django 3.2.4 on 2023-01-30 20:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0006_delete_auditlog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='professoralias',
            name='alias',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
