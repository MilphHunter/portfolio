from django import forms

from .models import Folder, UserTag


class TagForm(forms.ModelForm):
    tag_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Name',
            'data-sb-validations': 'required',
        })
    )

    class Meta:
        model = UserTag
        fields = ('tag_name',)

    def clean_tag_name(self):
        tag_name = self.cleaned_data['tag_name']
        if UserTag.objects.filter(tag_name=tag_name).exists():
            raise forms.ValidationError("Такой тег уже существует.")
        return tag_name


class FolderForm(forms.ModelForm):
    folder_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Name',
            'data-sb-validations': 'required',
            'onfocus': 'handleFocus()',
        })
    )
    folder_img = forms.ImageField(
        widget=forms.FileInput(attrs={
            'class': 'form-control d-none',
            'onchange': 'displaySelectedImage(event, "selectedImage")'
        }), required=False
    )
    folder_description = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Description',
        }), required=False
    )

    class Meta:
        model = Folder
        fields = ('folder_name', 'folder_img', 'folder_description')

    def clean_folder_name(self):
        folder_name = self.cleaned_data['folder_name']
        if Folder.objects.filter(folder_name=folder_name).exists():
            raise forms.ValidationError("Такая папка уже существует.")
        return folder_name


class PasswordInputForm(forms.Form):
    first_symbol = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control passEnter__input', 'aria-label': 'First number',
               'oninput': 'moveToNextInput(this, event)'}), max_length=1)
    second_symbol = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control passEnter__input', 'aria-label': 'Second number',
               'oninput': 'moveToNextInput(this, event)'}), max_length=1)
    third_symbol = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control passEnter__input', 'aria-label': 'Third number',
               'oninput': 'moveToNextInput(this, event)'}), max_length=1)
    fourth_symbol = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control passEnter__input', 'aria-label': 'Fourth number',
               'oninput': 'moveToNextInput(this, event)'}), max_length=1)


class SearchForm(forms.Form):
    query = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control me-2', 'placeholder': 'Знайти...', 'aria-label': 'Search', }))
