from django.urls import path

from .views import *

app_name = 'workspace'

urlpatterns = [
    path('', index, name='index'),
    path('all-notes/', all_notes, name='allNotes'),
    path('all-notes/put-in-safe/<int:note_id>/<str:path>/', put_note_in_safe, name='safePut'),
    path('all-notes/delete/<int:id>/<str:path>/', delete_note, name='noteDelete'),
    path('all-notes/tags/<str:tagsString>/', notes_sorted_tag, name='sortedNotesByTag'),
    path('all-folders/', all_folders, name='allFolders'),
    path('all-notes/folders/<int:id>/<str:folder_slug>/', notes_sorted_folder, name='sortedNotesByFolder'),
    path('all-folders/folders/pin-folder/<int:id>/<str:path>/', folder_pin, name='folderPin'),
    path('all-folders/folders/delete-folder/<int:id>', folder_delete, name='folderDelete'),
    path('safe-notes/check/', check_pass, name='checkPass'),
    path('safe-notes/', safe_notes, name='safeNotes'),
    path('safe-notes/tags/<str:tagsString>/', safe_sorted_tag, name='sortedNotesByTag'),
    path('all-notes/find/', post_search, name='findNotes')
]
