from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, DetailView, TemplateView
from .forms import RecipeForm, CommentForm
from blog.models import Post, Recipe, Comment, Category


class HomeView(TemplateView):
    template_name = "blog/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Главная"
        # Получаем три последние статьи
        latest_posts = Post.objects.order_by('-create_at')[:3]
        context['latest_posts'] = latest_posts
        # Получаем два лучших рецепта
        best_posts = Post.objects.order_by('-views')[:2]
        context['best_posts'] = best_posts
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
        Мы переопределяем этот метод, чтобы изменить порядок сортировки объектов Post по полю create_at в
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
        return context


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
