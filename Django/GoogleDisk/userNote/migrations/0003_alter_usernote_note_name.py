# Generated by Django 5.1 on 2024-08-26 10:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userNote', '0002_usernote_is_hide'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usernote',
            name='note_name',
            field=models.CharField(default='Моя думка', max_length=150),
        ),
    ]