from random import sample
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sessions.models import Session
from django.db.models import Value, CharField
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.generic import ListView, DetailView, TemplateView, CreateView, FormView
from unidecode import unidecode
from .forms import RecipeForm, CommentForm, PostForm, RecipeInlineFormSet, SubscriberForm
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
            recipe.rating = round(recipe.get_rating())
        context['random_recipes'] = random_recipes
        # Получаем рецепты с максимальным рейтингом
        top_rated_recipes = Recipe.objects.order_by('-views')[:9]
        # Добавляем изображение по умолчанию, если у рецепта нет фото
        for recipe in top_rated_recipes:
            if not recipe.image:
                recipe.image = recipe.get_image_url()
                # Добавляем рейтинг для каждого объекта рецепта
            recipe.rating = round(recipe.get_rating())
        context['top_rated_recipes'] = top_rated_recipes
        # Проверяем, доступен ли атрибут user в объекте request
        if hasattr(self.request, 'user'):
            context['can_share_recipe'] = self.request.user.is_authenticated
        else:
            context['can_share_recipe'] = False

        context['form'] = SubscriberForm()

        return context


class AllPostsListView(ListView):
    model = Post
    template_name = 'blog/all_posts.html'
    context_object_name = 'all_posts'
    ordering = ['-create_at']
    paginate_by = 5


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
        obj = super().get_object(queryset=queryset)

        # Получаем текущую сессию пользователя
        session_key = self.request.session.session_key

        # Получаем список всех сессий, в которых этот пользователь уже смотрел этот пост
        viewed_sessions = Session.objects.filter(
            expire_date__gte=timezone.now(),
            session_data__contains=obj.slug,
            session_key__in=self.request.session.keys()
        )

        # Если текущая сессия не присутствует в просмотренных сессиях, увеличиваем счетчик просмотров
        if session_key not in viewed_sessions.values_list('session_key', flat=True):
            obj.views += 1
            obj.save()
            # Добавляем текущую сессию в список просмотренных
            self.request.session[obj.slug] = True
            self.request.session.save()
        # Вызываем метод get_rating для отслеживания рейтинга поста
        obj.get_rating()
        print(obj)
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        context['title'] = self.object.title
        context['comment_form'] = CommentForm()
        context['create_at'] = self.object.create_at
        comments = post.comments.filter(post=post)
        context['comments'] = comments
        return context

    @login_required
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


@method_decorator(login_required, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class AddPostWithRecipeView(View):
    def get(self, request):
        post_form = PostForm()
        recipe_formset = RecipeInlineFormSet(instance=Post())
        return render(request, 'blog/add_post.html', {'post_form': post_form, 'recipe_formset': recipe_formset})

    def post(self, request):
        post_form = PostForm(request.POST, request.FILES)
        recipe_formset = RecipeInlineFormSet(request.POST, request.FILES, instance=Post())

        if post_form.is_valid() and recipe_formset.is_valid():
            post = post_form.save(commit=False)
            post.author = request.user
            slug_base = f"{slugify(unidecode(post.title))}-{post.category.pk}"
            slug = slug_base
            count = 1
            while Post.objects.filter(slug=slug).exists():
                slug = f"{slug_base}-{count}"
                count += 1
            post.slug = slug
            post.save()
            recipe_formset.instance = post
            recipe_formset.save()

            category_slug = post.category.slug
            url = reverse('post_single', kwargs={'slug': category_slug, 'post_slug': post.slug})
            return redirect(url)

        return render(
            request, 'blog/add_post.html',
            {'post_form': post_form, 'recipe_formset': recipe_formset}
        )


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


class AllRecipesListView(ListView):
    model = Recipe
    template_name = 'blog/all_recipes.html'
    context_object_name = 'all_recipes'
    ordering = ['-views']
    paginate_by = 5


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
        context['recipe'] = recipe
        context['comments'] = comments
        context['form'] = form
        context['title'] = title
        return context

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)

        # Получаем текущую сессию пользователя
        session_key = self.request.session.session_key

        # Получаем список всех сессий, в которых этот пользователь уже смотрел этот пост
        viewed_sessions = Session.objects.filter(
            expire_date__gte=timezone.now(),
            session_data__contains=obj.pk,
            session_key__in=self.request.session.keys()
        )

        # Если текущая сессия не присутствует в просмотренных сессиях, увеличиваем счетчик просмотров
        if session_key not in viewed_sessions.values_list('session_key', flat=True):
            obj.views += 1
            obj.save()
            # Добавляем текущую сессию в список просмотренных
            self.request.session[obj.pk] = True
            self.request.session.save()
        # Вызываем метод get_rating для отслеживания рейтинга поста
        obj.get_rating()
        return obj

    def post(self, request, *args, **kwargs):
        recipe = self.get_object()
        form = CommentForm(request.POST)
        if form.is_valid():
            if request.user.is_authenticated:
                comment = form.save(commit=False)
                comment.user = request.user
                comment.recipe = recipe
                comment.save()
                return redirect('recipe_detail', pk=recipe.pk)
            else:
                return redirect('login')
        context = self.get_context_data()
        return self.render_to_response(context)


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
        form.instance.user = self.request.user
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
    @staticmethod
    def post(request):
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

    @staticmethod
    def get(request):
        return render(request, 'blog/index.html')


class SubscribeView(FormView):
    template_name = 'index.html'
    form_class = SubscriberForm
    success_url = reverse_lazy('index')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class()
        return context


class ContactView(TemplateView):
    template_name = 'blog/contacts.html'


class AboutView(TemplateView):
    template_name = 'blog/about.html'
