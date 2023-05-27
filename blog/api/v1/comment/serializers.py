from rest_framework import serializers

from blog.models.comment import Comment


class CommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ('id', 'post', 'name', 'email', 'body')
