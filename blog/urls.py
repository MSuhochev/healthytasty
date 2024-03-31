from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='index'),
    path('add_recipe/', views.AddRecipeView.as_view(), name='add_recipe'),
    path('recipes/<slug:slug>/', views.RecipeListView.as_view(), name='recipe_list'),
    path('recipe/<int:pk>/', views.RecipeDetailView.as_view(), name='recipe_detail'),
    path('post/<slug:slug>/', views.PostListView.as_view(), name="post_list"),  # Префикс 'post/' добавлен
    path('post/<slug:slug>/<slug:post_slug>/', views.PostDetailView.as_view(), name="post_single"),
    # Префикс 'post/' добавлен
]
