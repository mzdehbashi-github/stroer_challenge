from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from blog.models.post import Post
from blog.models.comment import Comment


class TestCommentView(APITestCase):

    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.user = user_model.objects.create_user(username='myusername')
        cls.post = Post.objects.create(
            user_id=1,
            title='FakeTitle',
            body='FakeBody',
        )

        cls.comment = Comment.objects.create(
            post=cls.post,
            name='John Doe',
            email='johndoe@example.com',
            body='This is a comment.'
        )

    def test_list_comments(self):
        self.client.force_login(self.user)
        url = reverse('comment-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_create_comment(self):
        self.client.force_login(self.user)
        data = {
            'post': self.post.id,
            'name': 'Jane Smith',
            'email': 'janesmith@example.com',
            'body': 'Another comment.'
        }
        url = reverse('comment-list')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201, response.json())
        self.assertEqual(Comment.objects.filter(**data).count(), 1)

    def test_delete_comment(self):
        self.client.force_login(self.user)
        url = reverse('comment-detail', args=[self.comment.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Comment.objects.filter(id=self.comment.id).exists())

    def test_partial_update_comment(self):
        self.client.force_login(self.user)
        data = {'name': 'Updated Name'}
        url = reverse('comment-detail', args=[self.comment.id])
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.name, 'Updated Name')

    def test_retrieve_comment(self):
        self.client.force_login(self.user)
        url = reverse('comment-detail', args=[self.comment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], self.comment.name)
        self.assertEqual(response.data['email'], self.comment.email)
        self.assertEqual(response.data['body'], self.comment.body)
