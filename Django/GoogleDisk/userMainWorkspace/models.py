from django.contrib.auth.models import User
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from text_unidecode import unidecode


class UserTag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tag_name = models.CharField(max_length=100, default='Tag')
    tag_slug = models.SlugField(max_length=200, blank=True)
    tag_count = models.IntegerField(default=0)
    created = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.tag_slug:
            self.tag_slug = slugify(unidecode(self.tag_name))
        super().save(*args, **kwargs)


class Folder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    folder_name = models.CharField(max_length=100)
    folder_slug = models.SlugField(max_length=200, blank=True)
    folder_description = models.CharField(max_length=300, default='', blank=True)
    created = models.DateField(auto_now_add=True)
    folder_img = models.ImageField(upload_to='img/folder_img/', default='img/folder_img/folder-black.png', blank=True)
    is_pinned = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['-created']),
        ]
        ordering = ['-created']

    def save(self, *args, **kwargs):
        if not self.folder_slug:
            self.folder_slug = slugify(unidecode(self.folder_name))
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('images:detail', args=[self.id, self.folder_slug])
