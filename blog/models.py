from ckeditor.fields import RichTextField
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey


class Category(MPTTModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    parent = TreeForeignKey('self', related_name="children", on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

    class MPTTMeta:
        order_insertion_by = ['name']


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="posts", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='articles/', blank=True)
    text = RichTextField()
    category = models.ForeignKey(Category, related_name="post", on_delete=models.SET_NULL, null=True)
    tags = models.ManyToManyField(Tag, related_name="post")
    create_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(max_length=200, unique=True)
    views = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

    def get_absolute_url(self):

        if self.category:
            return reverse('post_single', kwargs={'post_slug': self.slug, 'slug': self.category.slug})
        # Если у поста нет категории, используем только slug поста в URL
        else:
            return reverse('post_single', kwargs={'post_slug': self.slug})

    def get_recipes(self):
        return self.recipes.all()

    def get_last_recipes(self):
        return self.recipes.last()

    def get_rating(self):
        # Рассчитываем рейтинг на основе просмотров и количества комментариев
        total_views = self.views
        total_comments = self.comments.count()  # количество комментариев
        rating = (total_views + total_comments) / 2  # расчет рейтинга
        return rating


class Recipe(models.Model):
    name = models.CharField(max_length=100)
    serves = models.CharField(max_length=50)
    prep_time = models.PositiveIntegerField(default=0)
    cook_time = models.PositiveIntegerField(default=0)
    ingredients = RichTextField()
    directions = RichTextField()
    image = models.ImageField(upload_to='recipe_images/', blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="recipes_added", on_delete=models.SET_NULL,
                               null=True)
    category = models.ForeignKey(Category, related_name="recipes", on_delete=models.SET_NULL, null=True)
    create_at = models.DateTimeField(auto_now_add=True)
    post = models.ForeignKey(Post, related_name="recipes", on_delete=models.SET_NULL, null=True, blank=True)
    views = models.PositiveIntegerField(default=0)  # Поле для отслеживания просмотров

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.author and self.post:
            self.author = self.post.author
        if self.post:
            self.image = self.post.image  # Используем изображение статьи, если оно есть
        super().save(*args, **kwargs)

    def get_image_url(self):
        if self.image:
            return self.image.url
        else:
            return "/recipe_images/default_recipe_image.jpg"

    def get_absolute_url(self):
        return reverse('recipe_detail', kwargs={'pk': self.pk})

    def get_rating(self):
        # Рассчитываем рейтинг на основе просмотров и количества комментариев
        total_views = self.views
        total_comments = self.comments.count()  # подсчитываем количество комментариев
        rating = (total_views + total_comments) / 2  # простой способ расчета рейтинга, можете выбрать свой
        return rating


class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="comments", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    email = models.CharField(max_length=80)
    message = models.TextField(max_length=500)
    create_at = models.DateTimeField(default=timezone.now)
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE, null=True, blank=True)
    recipe = models.ForeignKey(Recipe, related_name="comments", on_delete=models.CASCADE, null=True, blank=True)


class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
