# Generated by Django 5.1 on 2024-08-27 10:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userMainWorkspace', '0004_alter_folder_folder_img'),
    ]

    operations = [
        migrations.AlterField(
            model_name='folder',
            name='folder_img',
            field=models.ImageField(blank=True, default='static/vendor/content/img/folder-black.png', upload_to='img/folder_img/'),
        ),
    ]