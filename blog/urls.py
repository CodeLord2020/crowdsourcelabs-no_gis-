from django.urls import path 
from .views import * 

urlpatterns = [
    path('blogs/category',ListCreateBlogCategory.as_view()),
    path('blogs/category/<int:pk>',RetrieveBlogCategory.as_view()),
    path('blogs',ListBlogView.as_view()),
    path('blogs/create',CreateBlogView.as_view()),
    path('blogs/<int:pk>',RetrieveBlogView.as_view()),
    path('blogs/comment/create',CreateBlogComment.as_view()),
    path('blogs/<int:blog_id>/comments',ListAllBlogComment.as_view()),
    path('blogs/comment/<int:pk>',RetrieveBlogComment.as_view()),

]