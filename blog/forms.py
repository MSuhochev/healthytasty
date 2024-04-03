from ckeditor.widgets import CKEditorWidget
from django import forms
from django.forms import inlineformset_factory
from django.views import View

from .models import Recipe, Comment, Post


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


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'image', 'text', 'category', 'tags']
        widgets = {
            'author': forms.HiddenInput(),
            'text': forms.Textarea(attrs={'rows': 4}),  # Customize text area widget as needed
        }
        required = ['author']

    def clean(self):
        cleaned_data = super().clean()
        image = cleaned_data.get('image')
        if not image:
            cleaned_data['image'] = '/recipe_images/default_recipe_image.jpg'   # Дефолтная картинка
        return cleaned_data


class RecipeInlineForm(forms.ModelForm):
    class Meta:
        model = Recipe
        exclude = ['author', 'post', 'views']  # Exclude author and post fields as they will be set programmatically
        widgets = {
            'ingredients': forms.Textarea(attrs={'rows': 4}),  # Customize text area widget as needed
            'directions': forms.Textarea(attrs={'rows': 4}),  # Customize text area widget as needed
        }


RecipeInlineFormSet = inlineformset_factory(Post, Recipe, fields=['name', 'serves', 'prep_time', 'cook_time', 'ingredients', 'directions', 'image', 'category'], extra=1)


# In your view where you handle the form submission:

