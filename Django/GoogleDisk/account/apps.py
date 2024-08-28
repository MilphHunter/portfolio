import os
import shutil

from django.apps import AppConfig
from django.conf import settings


class AccountConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'account'

    # Create folder for save files
    def ready(self):
        directories = [
            os.path.join(settings.BASE_DIR, 'content', 'img', 'folder_img'),
            os.path.join(settings.BASE_DIR, 'content', 'files', 'audio', 'covers'),
        ]

        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"Create directory: {directory}")

        # Copy default folder img
        source_file = os.path.join(settings.BASE_DIR, 'static', 'vendor', 'content', 'img', 'folder-black.png')
        destination_directory = os.path.join(settings.BASE_DIR, 'content', 'img', 'folder_img')
        destination_file = os.path.join(destination_directory, 'folder-black.png')

        if os.path.exists(source_file):
            shutil.copy(source_file, destination_file)
            print(f"File {source_file} copy in {destination_file}")
        else:
            print(f"File {source_file} isn't exist")
