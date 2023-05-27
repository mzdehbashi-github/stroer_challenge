from django.db import models
from django.conf import settings


class Comment(models.Model):
    post = models.ForeignKey('blog.Post', on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    email = models.EmailField()
    body = models.TextField()

    @staticmethod
    def update_delete_url(item_id):
        return f'{settings.COMMENTS_URL}/{item_id}'

    @staticmethod
    def list_create_url():
        return settings.COMMENTS_URL

    @property
    def serialized_value(self):
        return {
            'postId': self.post_id,
            'name': self.name,
            'email': self.email,
            'body': self.body,
        }
