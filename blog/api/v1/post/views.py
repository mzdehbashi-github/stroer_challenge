from rest_framework.viewsets import ModelViewSet

from blog.models.post import Post
from blog.api.v1.post.serializers import PostSerializer


class PostView(ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
