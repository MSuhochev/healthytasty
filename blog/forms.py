from ckeditor.widgets import CKEditorWidget
from django import forms
from django.forms import inlineformset_factory
from django.views import View

from .models import Recipe, Comment, Post, Subscriber, Tag


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
    tags = forms.CharField(max_length=200, required=False, help_text='Введите теги через запятую.', label='Теги')
    existing_tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Выбрать существующие теги'
    )

    class Meta:
        model = Post
        fields = ['title', 'image', 'text', 'category', 'tags', 'existing_tags']
        widgets = {
            'author': forms.HiddenInput(),
            'text': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'title': 'Заголовок',
            'image': 'Изображение',
            'text': 'Текст',
            'category': 'Выбрать категорию',
        }

    def clean_tags(self):
        data = self.cleaned_data['tags']
        tags = [tag.strip() for tag in data.split(',') if tag.strip()]
        return tags

    def clean(self):
        cleaned_data = super().clean()
        image = cleaned_data.get('image')
        if not image:
            cleaned_data['image'] = '/recipe_images/default_recipe_image.jpg'   # Дефолтная картинка
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()  # Сохраняем теги после сохранения экземпляра
        return instance


class RecipeInlineForm(forms.ModelForm):
    class Meta:
        model = Recipe
        exclude = ['author', 'post', 'views']  # Exclude author and post fields as they will be set programmatically
        widgets = {
            'ingredients': forms.Textarea(attrs={'rows': 4}),  # Customize text area widget as needed
            'directions': forms.Textarea(attrs={'rows': 4}),  # Customize text area widget as needed
        }


RecipeInlineFormSet = inlineformset_factory(
    Post, Recipe,
    fields=['name', 'serves', 'prep_time', 'cook_time', 'ingredients', 'directions', 'image', 'category'],
    extra=1,
    labels={
        'name': 'Название',
        'serves': 'Количество персон',
        'prep_time': 'Время подготовки мин.',
        'cook_time': 'Время приготовления мин.',
        'ingredients': 'Ингредиенты',
        'directions': 'Приготовление',
        'image': 'Выбрать изображение',
        'category': 'Выбрать категорию',
    }
)


class SubscriberForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ['email']

