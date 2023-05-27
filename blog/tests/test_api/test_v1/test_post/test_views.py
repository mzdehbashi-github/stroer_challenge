from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from blog.models.post import Post


class TestPostView(APITestCase):

    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.user = user_model.objects.create_user(username='myusername')
        cls.post = Post.objects.create(user_id=12345, title='Existing Post', body='Existing post body')

    def test_create_post(self):
        url = reverse('post-list')
        data = {
            'title': 'Test Post',
            'body': 'This is a test post.',
        }
        self.client.force_login(self.user)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.filter(**data, user_id=99999942).count(), 1)

    def test_retrieve_post(self):
        url = reverse('post-detail', args=[self.post.id])
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], self.post.title)
        self.assertEqual(response.data['id'], self.post.id)
        self.assertEqual(response.data['body'], self.post.body)
        self.assertEqual(response.data['user_id'], self.post.user_id)

    def test_list_posts(self):
        url = reverse('post-list')
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_partial_update_post(self):
        url = reverse('post-detail', args=[self.post.id])
        data = {'title': 'Updated Title'}
        self.client.force_login(self.user)
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated Title')

    def test_delete_post(self):
        url = reverse('post-detail', args=[self.post.id])
        self.client.force_login(self.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), 0)


