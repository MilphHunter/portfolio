import json
import os
import re

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3

from userMainWorkspace.models import Folder, UserTag
from userNote.forms import NoteCreateForm, TemplateContentAdd
from userNote.models import TemplateUserNoteContent, UserNote


def file_input(request):
    img = ['.jpeg', '.jpg', '.jpe', '.jfif', '.ico', '.png', '.gif', '.svg', '.tiff', '.tif', '.webp', '.eps']
    video = ['.mov', '.mpeg4', '.mp4', '.MP4', '.avi', '.wmv', '.mpegps', '.flv', '.3gpp', 'webm']
    audio = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.m4r', '.aiff', '.wma', '.amr', '.midi']
    for file in request.FILES.getlist('file'):
        dot_index = file.name.rfind('.')
        extension = file.name[dot_index:]
        if extension in img:
            upload_folder = os.path.join(settings.MEDIA_ROOT, 'files/img/')
            fs = FileSystemStorage(location=upload_folder)
            fs.save(file.name, file)
            bd_add = TemplateUserNoteContent(note_img=f'files/img/{file.name}', user=request.user)
            bd_add.save()
        elif extension in video:
            upload_folder = os.path.join(settings.MEDIA_ROOT, 'files/video/')
            fs = FileSystemStorage(location=upload_folder)
            fs.save(file.name, file)
            bd_add = TemplateUserNoteContent(note_video=f'files/video/{file.name}', user=request.user)
            bd_add.save()
        elif extension in audio:
            upload_folder = os.path.join(settings.MEDIA_ROOT, 'files/audio/')
            fs = FileSystemStorage(location=upload_folder)
            fs.save(file.name, file)
            file_path = os.path.join(settings.MEDIA_ROOT, f'files/audio/{file.name}')
            title, artist, audio_cover = get_music_metadata(file_path)
            if title == '':
                title = file.name
            bd_add = TemplateUserNoteContent(note_audio=file_path, note_audio_title=title, note_audio_author=artist,
                                             note_audio_image=audio_cover, user=request.user)
            bd_add.save()
        else:
            upload_folder = os.path.join(settings.MEDIA_ROOT, 'files/other/')
            upload_file_size = 1 if round(file.size / 1_000_000) < 1 else round(file.size / 1_000_000)
            fs = FileSystemStorage(location=upload_folder)
            fs.save(file.name, file)
            bd_add = TemplateUserNoteContent(note_other=f'{file.name}', note_other_size=upload_file_size,
                                             user=request.user)
            bd_add.save()
    note_id = request.POST.get('noteId')
    data_files = TemplateUserNoteContent.objects.filter(user=request.user)
    files = {'note_img': [], 'note_video': [], 'note_audio': [], 'note_other': []}
    for data in data_files:
        if data.note_img != '':
            files['note_img'].append(data.note_img.url)
        if data.note_video != '':
            files['note_video'].append(data.note_video.url)
        if data.note_audio != '':
            audio = {'note_audio': str(data.note_audio), 'note_audio_url': data.note_audio.url,
                     'note_audio_title': data.note_audio_title, 'note_audio_author': data.note_audio_author,
                     'note_audio_img': data.note_audio_image}
            files['note_audio'].append(audio)
        if data.note_other != '':
            other = {'note_other': data.note_other.url, 'note_other_name': str(data.note_other),
                     'note_other_size': data.note_other_size}
            files['note_other'].append(other)
    if note_id:
        bd = UserNote.objects.get(id=note_id)
        bd_files = bd.note_file
        for file in files['note_img']:
            bd_files['note_img'].append(file)
        for file in files['note_video']:
            bd_files['note_video'].append(file)
        for file in files['note_audio']:
            audio = {'note_audio': file['note_audio_url'], 'note_audio_title': file['note_audio_title'],
                     'note_audio_author': file['note_audio_author'], 'note_audio_image': file['note_audio_img']}
            bd_files['note_audio'].append(audio)
        for file in files['note_other']:
            other = {'note_other': file['note_other'], 'note_other_name': file['note_other_name'],
                     'note_other_size': file['note_other_size']}
            bd_files['note_other'].append(other)
        bd.note_file = bd_files
        bd.save()
        TemplateUserNoteContent.objects.filter(user=request.user).delete()
        files = bd.note_file
    return JsonResponse({'files': files}, status=200)


class CreateNote(FormView):
    template_name = 'userNote/note/note_create.html'
    form_class = TemplateContentAdd
    success_url = reverse_lazy('note:createNote')

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        pass

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'NoteCreate'
        context['form_note'] = NoteCreateForm()
        context['form_note_template'] = self.get_form()
        context['template_content'] = (TemplateUserNoteContent.objects.filter(user=self.request.user))[::-1]
        context['included_tags'] = get_included_tags(self.request)
        context['tags'] = UserTag.objects.filter(user=self.request.user)
        context['folders'] = Folder.objects.filter(user=self.request.user)
        return context


def get_music_metadata(file_path):
    try:
        audio = EasyID3(file_path)
        title = audio.get('title', [''])[0]
        artist = audio.get('artist', [''])[0]
        try:
            audio = ID3(file_path)
            images = audio.getall('APIC')
            if images:
                image_data = images[0].data
                image_format = images[0].mime.split('/')[-1]
                output_path = os.path.join(settings.MEDIA_ROOT, 'files/audio/covers/',
                                           f'{clean_filename(title)}-{clean_filename(artist)}.{image_format}')
                with open(output_path, 'wb') as img_file:
                    img_file.write(image_data)
                    audio_cover = os.path.join(
                        f'/content/files/audio/covers/{clean_filename(title)}-{clean_filename(artist)}.{image_format}')
        except Exception as e:
            print(f"An error occurred: {e}")
        return title, artist, audio_cover
    except Exception as e:
        print(f"Ошибка при получении метаданных: {e}")
        return '', '', ''


def clean_filename(s):
    return re.sub(r'[\/:*?"<>|]', '_', s)


def assign_tag_to_note_template(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        tag_id = data.get('tag_id')
        note_id = data.get('note_id')
        tag_exist_template = TemplateUserNoteContent.objects.filter(note_tag__id=tag_id).exists()
        tag_exist = False
        if note_id.isnumeric():
            tag_exist = UserNote.objects.filter(note_tag__id=tag_id, id=note_id).exists()
        tag = get_object_or_404(UserTag, id=tag_id)
        if tag_exist_template or tag_exist:
            user_notes = False
            if note_id.isnumeric():
                user_notes = UserNote.objects.filter(user=request.user, id=note_id)
            if user_notes:
                for user_note in user_notes:
                    user_note.note_tag.remove(tag)
            else:
                user_note_templates = TemplateUserNoteContent.objects.filter(user=request.user)
                for user_note_template in user_note_templates:
                    user_note_template.note_tag.remove(tag)
        else:
            user_notes = False
            if note_id.isnumeric():
                user_notes = UserNote.objects.filter(user=request.user, id=note_id)
            if user_notes:
                for user_note in user_notes:
                    user_note.note_tag.add(tag)
            else:
                user_note_template = TemplateUserNoteContent.objects.create(user=request.user)
                user_note_template.note_tag.add(tag)
        return JsonResponse({'tag_count': str(get_tag_count(request, tag_id))})


def get_tag_count(request=None, tag_id=0, safe=False):
    if tag_id == 0:
        user_tags = UserTag.objects.filter(user=request.user)
        if safe:
            for user_tag in user_tags:
                user_tag.tag_count = user_tag.usernote_set.filter(user=request.user, is_hide=True).count()
                user_tag.save()
        else:
            for user_tag in user_tags:
                user_tag.tag_count = user_tag.usernote_set.filter(user=request.user, is_hide=False).count()
                user_tag.save()
    else:
        user_tag = UserTag.objects.get(pk=tag_id)
        user_tag_count = user_tag.usernote_set.all().count()
        template_count = user_tag.templateusernotecontent_set.all().count()
        user_tag.tag_count = user_tag_count + template_count
        user_tag.save()
        return user_tag.tag_count


def final_cut(request):
    if request.method == 'POST':
        form = NoteCreateForm(request.POST)
        if form.is_valid():
            form.instance.user = request.user
            form.save()
            safe_tags(request)
            safe_folder(request)
            safe_files(request)
    return redirect('workspace:index')


def safe_tags(request):
    template_contents = TemplateUserNoteContent.objects.filter(user=request.user)
    for template_content in template_contents:
        note_tags = template_content.note_tag.all()
        if note_tags:
            for note_tag in note_tags:
                user_note = UserNote.objects.filter(user=request.user).last()
                user_note.note_tag.add(note_tag.id)


def safe_folder(request):
    bd_add = UserNote.objects.filter(user=request.user).last()
    bd = TemplateUserNoteContent.objects.filter(user=request.user)
    bd = Folder.objects.filter(templateusernotecontent__in=bd)
    try:
        folder_id = bd.first().id
        folder = Folder.objects.get(id=folder_id)
        bd_add.note_folder.add(folder)
    except AttributeError:
        pass
    bd_add.save()


def safe_files(request):
    bd_add = UserNote.objects.filter(user=request.user).last()
    bd = TemplateUserNoteContent.objects.filter(user=request.user)
    file_dict = {'note_img': [], 'note_video': [], 'note_audio': [], 'note_other': []}
    for d in bd:
        if d.note_img:
            file_dict['note_img'].append(d.note_img.url)
        elif d.note_video:
            file_dict['note_video'].append(d.note_video.url)
        elif d.note_audio:
            inner_dict = {'note_audio': d.note_audio.url, 'note_audio_title': d.note_audio_title,
                          'note_audio_author': d.note_audio_author, 'note_audio_image': d.note_audio_image}
            file_dict['note_audio'].append(inner_dict)
        elif d.note_other:
            inner_dict = {'note_other': d.note_other.url, 'note_other_name': str(d.note_other),
                          'note_other_size': d.note_other_size}
            file_dict['note_other'].append(inner_dict)
    bd_add.note_file = file_dict
    bd_add.save()
    bd.delete()


def delete_files(request):
    if request.method == 'POST':
        file_to_delete = request.POST.get('fileToDelete')
        file_type = request.POST.get('fileType')
        note_id = request.POST.get('noteId')
        if note_id:
            file = UserNote.objects.get(id=note_id)
            file_list = file.note_file
            if file_type == 'note_audio':
                for cell in file_list['note_audio']:
                    if cell['note_audio'] == file_to_delete:
                        file_list['note_audio'].remove(cell)
                        break
            elif file_type == 'note_other':
                for cell in file_list['note_other']:
                    if cell['note_other'] == file_to_delete:
                        file_list['note_other'].remove(cell)
                        break
            else:
                file_list[file_type].remove(file_to_delete)
            file.note_file = file_list
            file.save()
            return JsonResponse({'message': 'File deleted successfully'})
        if file_to_delete.startswith('/content/'):
            file_to_delete = file_to_delete[9:]
        if file_type == 'img':
            TemplateUserNoteContent.objects.filter(note_img=file_to_delete, user=request.user).first().delete()
        elif file_type == 'video':
            TemplateUserNoteContent.objects.filter(note_video=file_to_delete, user=request.user).first().delete()
        elif file_type == 'audio':
            TemplateUserNoteContent.objects.filter(note_audio=file_to_delete, user=request.user).first().delete()
        elif file_type == 'other':
            TemplateUserNoteContent.objects.filter(note_other=file_to_delete, user=request.user).first().delete()
    return JsonResponse({'message': 'File deleted successfully'})


def delete_func(bd, file_type, file_to_delete, user):
    if file_type == 'img':
        bd.objects.filter(note_img=file_to_delete, user=user).first().delete()
    elif file_type == 'video':
        bd.objects.filter(note_video=file_to_delete, user=user).first().delete()
    elif file_type == 'audio':
        bd.objects.filter(note_audio=file_to_delete, user=user).first().delete()
    elif file_type == 'other':
        bd.objects.filter(note_other=file_to_delete, user=user).first().delete()


def get_folder_name(request):
    if request.method == 'POST':
        folder_name = request.POST.get('folder_name')
        folder = get_object_or_404(Folder, folder_name=folder_name)
        note_folder = TemplateUserNoteContent.objects.create(user=request.user)
        note_folder.note_folder.add(folder)
        note_folder.save()


class UpdateNote(FormView):
    template_name = 'userNote/note/note_update.html'
    form_class = NoteCreateForm
    success_url = reverse_lazy('note:createNote')

    def get(self, request, *args, **kwargs):
        TemplateUserNoteContent.objects.all().delete()
        note_id = kwargs['id']
        slug = kwargs['slug']
        note = get_object_or_404(UserNote, id=note_id, note_slug=slug, user=self.request.user)
        form = self.form_class(initial={'note_name': note.note_name, 'note_content': note.note_content})
        folder_name, folder_img = get_folder(request, note_id)
        context = self.get_context_data()
        context['form_note'] = form
        context['included_tags'] = get_included_tags(self.request, note_id)
        context['folder_name'] = folder_name
        context['folder_img'] = folder_img
        user_files = UserNote.objects.get(id=note_id)
        context['user_note'] = user_files
        context['content_img'] = user_files.note_file.get('note_img', [])
        context['content_video'] = user_files.note_file.get('note_video', [])
        context['content_audio'] = user_files.note_file.get('note_audio', [])
        context['content_other'] = user_files.note_file.get('note_other', [])
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        pass

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'NoteUpdate'
        context['form_note'] = NoteCreateForm()
        context['form_note_template'] = self.get_form()
        context['tags'] = UserTag.objects.filter(user=self.request.user)
        context['folders'] = Folder.objects.filter(user=self.request.user)
        return context


def get_folder(request, note_id):
    note = UserNote.objects.filter(user=request.user, id=note_id)
    try:
        folder = Folder.objects.get(user=request.user, usernote__in=note)
        folder_name = folder.folder_name
        folder_img = folder.folder_img.url
    except ObjectDoesNotExist:
        return ''
    return folder_name, folder_img

def get_included_tags(request, note_id=0):
    if note_id != 0:
        note = UserNote.objects.filter(user=request.user, id=note_id)
        tags = UserTag.objects.filter(usernote__in=note)
        tag_list = []
        for tag in tags:
            tag_list.append(tag.id)
    else:
        note = TemplateUserNoteContent.objects.filter(user=request.user)
        tags = UserTag.objects.filter(templateusernotecontent__in=note)
        tag_list = []
        for tag in tags:
            tag_list.append(tag.id)
    return tag_list


def note_update(request, id, slug):
    instance = UserNote.objects.get(pk=id)
    if request.method == 'POST':
        form = NoteCreateForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            update_folder(request, id)
    return redirect('workspace:index')


def update_folder(request, note_id):
    bd_add = UserNote.objects.get(user=request.user, id=note_id)
    with transaction.atomic():
        bd_add.note_folder.clear()
    bd = TemplateUserNoteContent.objects.filter(user=request.user)
    bd = Folder.objects.filter(templateusernotecontent__in=bd)
    try:
        folder_id = bd.first().id
        folder = Folder.objects.get(id=folder_id)
        bd_add.note_folder.add(folder)
    except AttributeError:
        pass
    bd_add.save()
