from django.urls import path

from .views import *

app_name = 'note'

urlpatterns = [
    path('', CreateNote.as_view(), name='createNote'),
    path('<int:id>/<slug:slug>/', UpdateNote.as_view(), name='updateNote'),
    path('upload/', file_input, name='fileInput'),
    path('add-tag/', assign_tag_to_note_template, name='addTag'),
    path('add-folder/', get_folder_name, name='addFolder'),
    path('file-delete/', delete_files, name='delFile'),
    path('add/', final_cut, name='addNote'),
    path('<int:id>/<slug:slug>/update', note_update, name='updateNoteConfirm'),
]
