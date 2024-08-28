from django.contrib.auth.decorators import login_required
from django.contrib.postgres.search import (SearchQuery, SearchRank,
                                            SearchVector)
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django.db.models import Case, When
from django.shortcuts import redirect, render

from account.models import Profile
from userNote.models import TemplateUserNoteContent, UserNote
from userNote.views import get_tag_count

from .forms import FolderForm, PasswordInputForm, SearchForm, TagForm
from .models import Folder, UserTag


@login_required
def index(request, pin_count=0):
    if request.method == 'POST':
        if 'tag_name' in request.POST:
            form = TagForm(request.POST)
            create_tag_folder(form, request)
        elif 'folder_name' in request.POST:
            form = FolderForm(request.POST, request.FILES)
            create_tag_folder(form, request)
    if request.method == 'POST' and 'clear_template_data' in request.POST:
        TemplateUserNoteContent.objects.filter(user=request.user).delete()
        return redirect('note:createNote')
    get_tag_count(request)
    form_tag = TagForm()
    form_folder = FolderForm()
    search_form = SearchForm()
    pin_count = pin_counter()
    password_input = PasswordInputForm()
    tags = UserTag.objects.filter(user=request.user)
    folders = folders = Folder.objects.filter(user=request.user).annotate(
        pinned_priority=Case(
            When(is_pinned=True, then=0),
            default=1,
            output_field=models.IntegerField(),
        )
    ).order_by('pinned_priority', '-created')
    notes = UserNote.objects.filter(user=request.user, is_hide=False).order_by('-updated')
    notes_unsorted = UserNote.objects.filter(note_folder__isnull=True, user=request.user).order_by('-created')
    content = {
        'title': 'Мій нотатник',
        'tags': tags,
        'folders': folders,
        'form_tag': form_tag,
        'form_folder': form_folder,
        'search_form': search_form,
        'password_input': password_input,
        'notes': notes,
        'notes_unsorted': notes_unsorted,
        'folders_pin': pin_count,
    }
    return render(request, 'workspaces/workspace/workspace.html', context=content)


def create_tag_folder(form, request):
    if form.is_valid():
        form.instance.user = request.user
        form.save()
        return redirect('workspace:index')


@login_required
def all_notes(request, tag_ids=None, folder_id=None):
    get_tag_count(request)
    tags = UserTag.objects.filter(user=request.user)
    folders = Folder.objects.filter(user=request.user)
    notes = UserNote.objects.filter(user=request.user, is_hide=False).order_by('-updated')
    password_input = PasswordInputForm()
    search_form = SearchForm()
    included_tags = []
    if tag_ids:
        filtered_notes = notes
        for tag_id in tag_ids:
            filtered_notes = filtered_notes.filter(note_tag__id=int(tag_id))
            included_tags.append(int(tag_id))
        notes = filtered_notes
    if folder_id:
        notes = UserNote.objects.filter(note_folder__id=folder_id)

    paginator = Paginator(notes, 12)
    page_number = request.GET.get('page', 1)
    try:
        notes = paginator.page(page_number)
    except PageNotAnInteger:
        notes = paginator.page(1)
    except EmptyPage:
        notes = paginator.page(paginator.num_pages)

    content = {
        'title': 'Мої записи',
        'tags': tags,
        'folders': folders,
        'notes': notes,
        'search_form': search_form,
        'included_tags': included_tags,
        'password_input': password_input,
    }
    return render(request, 'workspaces/workspace/all_notes.html', context=content)


def notes_sorted_tag(request, tagsString):
    tag_ids = tagsString.split(',')
    return all_notes(request, tag_ids=tag_ids)


def delete_note(request, id, path):
    if request.method == 'GET':
        UserNote.objects.get(id=id).delete()
        return redirect(path)
    return redirect(path)


@login_required
def all_folders(request, pin_count=0):
    tags = UserTag.objects.filter(user=request.user)
    password_input = PasswordInputForm()
    folders = Folder.objects.filter(user=request.user).annotate(
        pinned_priority=Case(
            When(is_pinned=True, then=0),
            default=1,
            output_field=models.IntegerField(),
        )
    ).order_by('pinned_priority', '-created')
    pin_count = pin_counter()
    search_form = SearchForm()
    paginator = Paginator(folders, 12)
    page_number = request.GET.get('page', 1)
    try:
        folders = paginator.page(page_number)
    except PageNotAnInteger:
        folders = paginator.page(1)
    except EmptyPage:
        folders = paginator.page(paginator.num_pages)

    content = {
        'title': 'Мої записи',
        'tags': tags,
        'folders': folders,
        'search_form': search_form,
        'folders_pin': pin_count,
        'password_input': password_input,
    }
    return render(request, 'workspaces/workspace/all_folders.html', context=content)


def pin_counter():
    pin_count = 0
    for f in Folder.objects.all():
        if f.is_pinned:
            pin_count += 1
    return pin_count


def notes_sorted_folder(request, id, folder_slug):
    return all_notes(request, folder_id=id)


def folder_pin(request, id, path):
    pin_folder_count = 0
    for f in Folder.objects.all():
        if f.is_pinned:
            pin_folder_count += 1
    if pin_folder_count <= 5:
        folder = Folder.objects.get(id=id)
        if pin_folder_count == 5:
            folder.is_pinned = False
        else:
            if folder.is_pinned:
                folder.is_pinned = False
            else:
                folder.is_pinned = True
        folder.save()
        return redirect(path)
    else:
        return redirect(path)


def folder_delete(request, id):
    folder_to_delete = Folder.objects.get(id=id)
    user_notes_to_delete = UserNote.objects.filter(note_folder=folder_to_delete)
    user_notes_to_delete.delete()
    folder_to_delete.delete()
    return redirect('workspaces:allFolders')


@login_required
def check_pass(request):
    if request.method == 'POST':
        password_form = PasswordInputForm(request.POST)
        entered_password = ''
        for num in password_form:
            entered_password += num.value()
        if Profile.objects.get(user=request.user).userPin == entered_password:
            return redirect('workspaces:safeNotes')
        else:
            return redirect('workspace:index')
    return redirect('workspace:index')


def safe_notes(request, tag_ids=None):
    get_tag_count(request, safe=True)
    password_input = PasswordInputForm()
    tags = UserTag.objects.filter(user=request.user)
    folders = Folder.objects.filter(user=request.user)
    search_form = SearchForm()
    notes = UserNote.objects.filter(user=request.user, is_hide=True).order_by('-updated')
    included_tags = []
    if tag_ids:
        filtered_notes = notes
        for tag_id in tag_ids:
            filtered_notes = filtered_notes.filter(note_tag__id=int(tag_id))
            included_tags.append(int(tag_id))
        notes = filtered_notes
    paginator = Paginator(notes, 12)
    page_number = request.GET.get('page', 1)
    try:
        notes = paginator.page(page_number)
    except PageNotAnInteger:
        notes = paginator.page(1)
    except EmptyPage:
        notes = paginator.page(paginator.num_pages)

    content = {
        'title': 'Приховані записи',
        'tags': tags,
        'folders': folders,
        'search_form': search_form,
        'notes': notes,
        'included_tags': included_tags,
        'password_input': password_input,
    }
    return render(request, 'workspaces/workspace/safe_notes.html', context=content)


def safe_sorted_tag(request, tagsString):
    tag_ids = tagsString.split(',')
    return safe_notes(request, tag_ids=tag_ids)


def put_note_in_safe(request, note_id, path):
    if request.method == 'GET':
        note = UserNote.objects.get(id=note_id)
        if not note.is_hide:
            note.is_hide = True
        else:
            note.is_hide = False
        note.save()
        return redirect(path)
    return redirect(path)


def post_search(request):
    tags = UserTag.objects.filter(user=request.user)
    search_form = SearchForm()
    query = None
    results = []
    if 'query' in request.GET:
        search_form = SearchForm(request.GET)
        if search_form.is_valid():
            query = search_form.cleaned_data['query']
            objects = UserNote.objects.filter(user=request.user)
            search_vector = SearchVector('note_name', 'note_content')
            search_query = SearchQuery(query)
            results = objects.annotate(search=search_vector, rank=SearchRank(search_vector, search_query)).filter(
                search=search_query).order_by('-rank')
    return render(request, 'workspaces/workspace/find_notes.html',
                  {'search_form': search_form, 'tags': tags, 'query': query, 'notes': results})
