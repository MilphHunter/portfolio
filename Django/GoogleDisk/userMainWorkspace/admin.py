from django.contrib import admin

from .models import Folder


@admin.register(Folder)
class ExistingFolders(admin.ModelAdmin):
    list_display = ['folder_name', 'user']
    prepopulated_fields = {'folder_slug': ('folder_name',)}
