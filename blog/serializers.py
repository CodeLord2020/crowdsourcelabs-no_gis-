from rest_framework import serializers
from .models import *
from cloud_resource.serializers import BlogResourceSerializer

class BlogCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogCategory
        fields = '__all__'



class BlogSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field='name', queryset=BlogCategory.objects.all())
    resource = BlogResourceSerializer(read_only=True)
    class Meta:
        model = Blog
        fields = ['id', 'title', 'author', 'content', 'category',
                   'created_at', 'resource']



class BlogCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogComment
        fields = '__all__'



class BlogSearchSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    category_name = serializers.SlugRelatedField(slug_field='name', queryset=BlogCategory.objects.all())

    class Meta:
        model = Blog
        fields = ['id', 'title', 'category', 'category_name', 'created_at', 'blogimage_url', 'author'] 

    def get_author(self, obj):
        return obj.author.first_name
