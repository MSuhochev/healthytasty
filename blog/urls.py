from django.urls import path
from . import views
from .views import AddCommentToRecipeView, AddCommentToPostView, SearchView, AddPostWithRecipeView

urlpatterns = [
    path('', views.HomeView.as_view(), name='index'),
    path('search/', SearchView.as_view(), name='search'),
    path('add_post/', AddPostWithRecipeView.as_view(), name='add_post'),
    path('add_recipe/', views.AddRecipeView.as_view(), name='add_recipe'),
    path('recipes/<slug:slug>/', views.RecipeListView.as_view(), name='recipe_list'),
    path('recipe/<int:pk>/', views.RecipeDetailView.as_view(), name='recipe_detail'),
    path('post/<slug:slug>/', views.PostListView.as_view(), name="post_list"),
    path('post/<slug:slug>/<slug:post_slug>/', views.PostDetailView.as_view(), name="post_single"),
    path('post/<slug:slug>/<slug:post_slug>/comment/', AddCommentToPostView.as_view(), name='add_comment_to_post'),
    path('recipe/<int:recipe_id>/comment/', AddCommentToRecipeView.as_view(), name='add_comment_to_recipe'),
]
