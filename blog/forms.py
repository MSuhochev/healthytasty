from ckeditor.widgets import CKEditorWidget
from django import forms
from .models import Recipe, Comment


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        labels = {
            "name": "Название",
            "serves": "Количество персон",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Введите название рецепта"}),
            'ingredients': CKEditorWidget(),
            'directions': CKEditorWidget(),
        }
        error_messages = {
            "name": {
                "required": "Введите название рецепта!",
            }
        }
        fields = ['name', 'serves', 'prep_time', 'cook_time', 'ingredients', 'directions', 'image', 'category']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'views' in self.fields:
            self.fields['views'].widget = forms.HiddenInput()


class CommentForm(forms.ModelForm):
    message = forms.CharField(widget=forms.Textarea, label='Введите ваш комментарий')

    class Meta:
        model = Comment
        fields = ['message']
