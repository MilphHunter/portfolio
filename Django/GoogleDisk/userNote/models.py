from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from django.urls import reverse
from text_unidecode import unidecode

from userMainWorkspace.models import Folder, UserTag


class UserNote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    note_name = models.CharField(max_length=150, default='Моя думка')
    note_content = models.TextField(blank=True, default='')
    note_file = models.JSONField(default=dict, blank=True)
    note_folder = models.ManyToManyField(Folder, blank=True)
    note_tag = models.ManyToManyField(UserTag, blank=True)
    note_slug = models.SlugField(max_length=200, blank=True)
    is_hide = models.BooleanField(default=0)
    created = models.DateField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.note_slug:
            self.note_slug = slugify(unidecode(self.note_name))
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('images:detail', args=[self.id, self.note_slug])


class TemplateUserNoteContent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    note_folder = models.ManyToManyField(Folder, blank=True)
    note_tag = models.ManyToManyField(UserTag, blank=True)
    note_img = models.FileField(upload_to='files/img/', default='', blank=True)
    note_video = models.FileField(upload_to='files/video/', default='', blank=True)
    note_audio = models.FileField(max_length=999, upload_to='files/audio/', default='', blank=True)
    note_audio_title = models.TextField(max_length=999, default='', blank=True)
    note_audio_author = models.TextField(max_length=999, default='', blank=True)
    note_audio_image = models.TextField(max_length=999, default='', blank=True)
    note_other = models.FileField(upload_to='files/other/', default='', blank=True)
    note_other_size = models.IntegerField(blank=True, default=0)
