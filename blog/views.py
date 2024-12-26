from django.shortcuts import render
from rest_framework import generics , status 
from rest_framework.response import Response
from .models import *
from .serializers import *
from .permissions import IsAuthenticatedOrReadOnly
from rest_framework.permissions import IsAuthenticated , IsAdminUser

# Create your views here.

class ListCreateBlogCategory(generics.ListCreateAPIView):
    queryset = BlogCategory.objects.all()
    serializer_class = BlogCategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class RetrieveBlogCategory(generics.RetrieveUpdateDestroyAPIView):
    queryset = BlogCategory.objects.all()
    serializer_class = BlogCategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class CreateBlogView(generics.CreateAPIView):
    queryset = Blog.objects.all()
    serializer_class =BlogSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    

class ListBlogView(generics.ListAPIView):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class RetrieveBlogView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class CreateBlogComment(generics.CreateAPIView):
    queryset = BlogComment.objects.all()
    serializer_class = BlogCommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ListAllBlogComment(generics.ListAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class=BlogCommentSerializer
    queryset = BlogComment.objects.none() 

    def get_queryset(self):
        blog_id = self.kwargs['blog_id']
        return BlogComment.objects.filter(blog=blog_id)


class RetrieveBlogComment(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = BlogComment.objects.all()
    serializer_class = BlogCommentSerializer