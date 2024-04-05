from django.urls import path
from . import views
from .views import AddCommentToRecipeView, AddCommentToPostView, SearchView, AddPostWithRecipeView, SubscribeView, \
    AboutView

urlpatterns = [
    path('', views.HomeView.as_view(), name='index'),  # главная
    path('search/', SearchView.as_view(), name='search'),  # поиск
    path('add_post/', AddPostWithRecipeView.as_view(), name='add_post'),  # добавить статью
    path('add_recipe/', views.AddRecipeView.as_view(), name='add_recipe'),  # добавить рецепт
    path('all_recipes/', views.AllRecipesListView.as_view(), name='all_recipes_list'),  # все рецепты
    path('recipes/<slug:slug>/', views.RecipeListView.as_view(), name='recipe_list'),  # все рецепты по категории
    path('recipe/<int:pk>/', views.RecipeDetailView.as_view(), name='recipe_detail'),  # рецепт детально
    path('all_posts/', views.AllPostsListView.as_view(), name='all_posts_list'),  # все статьи
    path('post/<slug:slug>/', views.PostListView.as_view(), name="post_list"),  # все статьи по категории
    path('post/<slug:slug>/<slug:post_slug>/', views.PostDetailView.as_view(), name="post_single"),  # статья детально
    # комментарии к статьям/рецептам
    path('post/<slug:slug>/<slug:post_slug>/comment/', AddCommentToPostView.as_view(), name='add_comment_to_post'),
    path('recipe/<int:recipe_id>/comment/', AddCommentToRecipeView.as_view(), name='add_comment_to_recipe'),
    # маршруты для редактирования материалов пользователя
    path('posts-and-recipes/', views.user_posts_and_recipes, name='user_posts_and_recipes'),
    path('edit-post/<int:post_id>/', views.edit_post, name='edit_post'),
    path('delete-post/<int:post_id>/', views.delete_post, name='delete_post'),
    path('edit-recipe/<int:recipe_id>/', views.edit_recipe, name='edit_recipe'),
    path('delete-recipe/<int:recipe_id>/', views.delete_recipe, name='delete_recipe'),
    # маршруты подписка/о проекте/контакты
    path('subscribe/', SubscribeView.as_view(), name='subscribe'),
    path('about/', AboutView.as_view(), name='about'),
    path('contacts/', views.ContactView.as_view(), name='contacts'),
]
