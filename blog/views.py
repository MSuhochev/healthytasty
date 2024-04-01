from random import sample
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Value, CharField
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, DetailView, TemplateView, CreateView
from .forms import RecipeForm, CommentForm
from blog.models import Post, Recipe, Comment, Category


class HomeView(TemplateView):
    template_name = "blog/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = "Введите текст для поиска по рецептам и постам..."
        context['title'] = "Главная"
        # Получаем три последних заметки
        latest_posts = Post.objects.order_by('-create_at')[:3]
        context['latest_posts'] = latest_posts
        # Получаем два лучших рецепта
        best_posts = Post.objects.order_by('-views')[:2]
        context['best_posts'] = best_posts
        # Добавляем 6 случайных рецептов
        random_recipes = sample(list(Recipe.objects.all()), min(Recipe.objects.count(), 6))
        # Добавляем изображение по умолчанию, если у рецепта нет фото
        for recipe in random_recipes:
            if not recipe.image:
                recipe.image = recipe.get_image_url()
        context['random_recipes'] = random_recipes
        # Проверяем, доступен ли атрибут user в объекте request
        if hasattr(self.request, 'user'):
            context['can_share_recipe'] = self.request.user.is_authenticated
        else:
            context['can_share_recipe'] = False

        return context


class PostListView(ListView):
    model = Post
    context_object_name = 'post_list'

    def get_queryset(self):
        return Post.objects.filter(category__slug=self.kwargs.get("slug")).select_related('category').order_by(
            '-create_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем объект категории
        category_slug = self.kwargs.get("slug")
        category = Category.objects.get(slug=category_slug)

        # Добавляем переменную title в контекст
        context['title'] = f"Заметки в категории {category.name}"

        return context


class PostDetailView(DetailView):
    """
    Это представление используется для отображения деталей поста, а также для отслеживания просмотров этого поста.
    """
    model = Post
    context_object_name = "post"
    slug_url_kwarg = "post_slug"
    template_name = 'blog/post_detail.html'

    def get_object(self, queryset=None):
        """
        Это метод, который позволяет настроить получение объекта перед его использованием в представлении.
        Переопределяем этот метод, чтобы изменить порядок сортировки объектов Post по полю create_at в
        порядке убывания.
        :param queryset:
        :return:
        """
        # Упорядочиваем объекты по полю 'create_at' в порядке убывания
        queryset = Post.objects.order_by('-create_at')
        obj = super().get_object(queryset=queryset)
        obj.views += 1
        obj.save()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.object.title
        context['comment_form'] = CommentForm()
        context['create_at'] = self.object.create_at
        context['can_share_recipe'] = True
        return context

    def post(self, request, *args, **kwargs):
        post_slug = self.kwargs.get('post_slug')
        post = get_object_or_404(Post, slug=post_slug)
        form = CommentForm(request.POST)
        if form.is_valid():
            form.instance.post = post
            form.instance.user = self.request.user
            form.save()
            # Перенаправляем на страницу поста с использованием post_slug
            return redirect('post_single', slug=post.category.slug, post_slug=post_slug)
        else:
            # Если форма невалидна, передаем ошибки обратно в контекст
            context = self.get_context_data()
            context['comment_form'] = form
            return self.render_to_response(context)


class AddRecipeView(View):
    """ Это представление AddRecipeView предназначено для добавления нового рецепта. """

    @method_decorator(login_required)
    def get(self, request):
        """ GET-запрос для отображения формы добавления рецепта"""
        form = RecipeForm()
        title = "Новый рецепт"
        context = {
            "title": title,
            "form": form,
        }
        return render(request, 'blog/add_recipe.html', context)

    @method_decorator(login_required)
    def post(self, request):
        """POST-запрос для обработки отправленной формы добавления рецепта"""
        form = RecipeForm(request.POST)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.author = request.user
            recipe.save()
            return redirect('recipe_list', slug=recipe.category.slug)
        return render(request, 'blog/add_recipe.html', {'form': form})


class RecipeDetailView(DetailView):
    model = Recipe
    template_name = 'blog/recipe_detail.html'
    context_object_name = 'recipe'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipe = self.get_object()
        comments = recipe.comments.all()
        form = CommentForm()
        title = recipe.name
        context['comments'] = comments
        context['form'] = form
        context['title'] = title
        return context

    def post(self, request, *args, **kwargs):
        recipe = self.get_object()
        comments = recipe.comments.all()
        form = CommentForm(request.POST)
        if form.is_valid():
            if request.user.is_authenticated:
                comment = form.save(commit=False)
                comment.user = request.user
                comment.recipe = recipe
                comment.post = recipe.post
                comment.save()
                return redirect('recipe_detail', pk=recipe.pk)
            else:
                return redirect('login')
        return self.render_to_response(self.get_context_data(form=form, comments=comments))


class RecipeListView(ListView):
    model = Recipe
    template_name = 'blog/recipe_list.html'
    context_object_name = 'recipes'

    def get_queryset(self):
        # Фильтрация рецептов по категории, определенной в URL-адресе
        category_slug = self.kwargs.get("slug")
        try:
            category = Category.objects.get(slug=category_slug)
        except Category.DoesNotExist:
            raise Http404("Category does not exist")
        return Recipe.objects.filter(category=category).order_by('-views')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs.get("slug")
        category = Category.objects.get(slug=category_slug)
        context['category'] = category
        context['title'] = f"Рецепты категории '{category.name}'"
        return context


class CommentHandlingMixin:
    @staticmethod
    def handle_comment_submission(self, request, form, **kwargs):
        if form.is_valid():
            comment = form.save(commit=False)
            if request.user.is_authenticated:
                comment.user = request.user
                comment.save()
            return True
        return False


class AddCommentToPostView(LoginRequiredMixin, CommentHandlingMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/post_detail.html'

    def form_valid(self, form):
        slug = self.kwargs.get('slug')
        post_slug = self.kwargs.get('post_slug')
        category = get_object_or_404(Category, slug=slug)
        post = get_object_or_404(Post, slug=post_slug, category=category)
        form.instance.post = post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('post_single', kwargs={'slug': self.kwargs['slug'], 'post_slug': self.kwargs['post_slug']})

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Оставлять комментарии могут только авторизованные пользователи.')
            return redirect('post_single', slug=self.kwargs['slug'], post_slug=self.kwargs['post_slug'])
        return super().get(request, *args, **kwargs)


class AddCommentToRecipeView(LoginRequiredMixin, CommentHandlingMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/recipe_detail.html'
    success_url = '/'

    def form_valid(self, form):
        recipe_id = self.kwargs['recipe_id']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        form.instance.recipe = recipe
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipe_id = self.kwargs['recipe_id']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        context['recipe'] = recipe
        return context

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Оставлять комментарии могут только авторизованные пользователи.')
            return redirect('recipe_detail', recipe_id=self.kwargs['recipe_id'])
        return super().get(request, *args, **kwargs)


class SearchView(View):
    def post(self, request):
        query = request.POST.get('search', None)
        if query:
            # Поиск по ингредиентам модели Recipe и названиям модели Post
            recipe_results = Recipe.objects.filter(ingredients__icontains=query)
            post_results = Post.objects.filter(title__icontains=query)
            # Получение краткого списка рецептов с использованием annotate
            recipe_results = recipe_results.annotate(
                search_type=Value('recipe', output_field=CharField())
            )

            # Получение краткого списка постов с использованием annotate
            post_results = post_results.annotate(
                search_type=Value('post', output_field=CharField())
            )
            context = {
                'recipe_results': recipe_results,
                'post_results': post_results,
                'query': query,
            }
            if recipe_results.exists() or post_results.exists():
                return render(request, 'blog/search_results.html', context)
            else:
                request.session['message'] = "По вашему запросу ничего не найдено."
                return redirect(reverse('index'))
        else:
            return redirect(reverse('index'))

    def get(self, request):
        return render(request, 'blog/index.html')
