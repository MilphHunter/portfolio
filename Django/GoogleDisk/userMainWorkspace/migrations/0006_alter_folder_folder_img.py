# Generated by Django 5.1 on 2024-08-27 10:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userMainWorkspace', '0005_alter_folder_folder_img'),
    ]

    operations = [
        migrations.AlterField(
            model_name='folder',
            name='folder_img',
            field=models.ImageField(blank=True, default='img/folder_img/folder-black.png', upload_to='img/folder_img/'),
        ),
    ]
