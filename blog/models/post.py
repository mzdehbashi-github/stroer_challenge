from django.db import models
from django.conf import settings


class Post(models.Model):
    user_id = models.PositiveBigIntegerField()
    title = models.CharField(max_length=256)
    body = models.TextField()

    @staticmethod
    def update_delete_url(item_id):
        return f'{settings.POSTS_URL}/{item_id}'

    @staticmethod
    def list_create_url():
        return settings.POSTS_URL

    @property
    def serialized_value(self):
        return {
            'userId': self.user_id,
            'title': self.title,
            'body': self.body,
        }
