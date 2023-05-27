from rest_framework.viewsets import ModelViewSet

from blog.models.comment import Comment
from blog.api.v1.comment.serializers import CommentSerializer


class CommentView(ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
