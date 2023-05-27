from rest_framework import serializers

from blog.models.post import Post


class PostSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(required=False)

    class Meta:
        model = Post
        fields = ('id', 'title', 'body', 'user_id')
        ref_name = 'V1PostSerializer'

    def validate(self, attrs):
        if self.context['view'].action == 'create':
            attrs['user_id'] = 99999942
        return attrs
