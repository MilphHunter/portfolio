from django import forms

from userNote.models import UserNote


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class NoteCreateForm(forms.ModelForm):
    note_name = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Мої думки',
               'aria - label': 'Username'}))
    note_content = forms.CharField(widget=forms.Textarea(
        attrs={'class': 'form-control text_area__main mb-3', 'style': 'height: 100px', 'title': 'Описание',
               'placeholder': 'Введите текст заметки'}), required=False)
    note_file = MultipleFileField(widget=MultipleFileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = UserNote
        fields = ('note_name', 'note_content', 'note_file')


class TemplateContentAdd(forms.Form):
    note_file = MultipleFileField(widget=MultipleFileInput(attrs={'class': 'form-control'}), required=False)