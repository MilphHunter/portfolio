# Generated by Django 5.1 on 2024-08-27 10:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userMainWorkspace', '0003_alter_folder_folder_name_alter_usertag_tag_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='folder',
            name='folder_img',
            field=models.ImageField(blank=True, default='img/folder_img/folder-black.png', upload_to='img/folder_img/'),
        ),
    ]