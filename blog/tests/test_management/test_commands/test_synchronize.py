from unittest import mock

from django.test import TestCase
from requests.exceptions import Timeout

from blog.models.post import Post
from blog.models.comment import Comment
from blog.management.commands.synchronize import Command


class FakeHttpResponse:

    def __init__(self, json_body):
        self._json = json_body

    def json(self):
        return self._json


def fake_requests_get(url: str, *args, **kwargs):
    if 'post' in url:
        return FakeHttpResponse(
            [
                {
                    "userId": 1,
                    "id": 1,
                    "title": "Title One",
                    "body": "Body One"
                },
                {
                    "userId": 2,
                    "id": 2,
                    "title": "Title Two",
                    "body": "Body Two"
                },
                {
                    "userId": 3,
                    "id": 3,
                    "title": "Title Three",
                    "body": "Body Three"
                },
            ]
        )
    else:
        return FakeHttpResponse(
            [
                {
                    "postId": 1,
                    "id": 1,
                    "name": "Name One",
                    "email": "email@one.com",
                    "body": "Body One"
                },
                {
                    "postId": 2,
                    "id": 2,
                    "name": "Name Two",
                    "email": "email@two.com",
                    "body": "Body Two"
                },
                {
                    "postId": 3,
                    "id": 3,
                    "name": "Name Three",
                    "email": "email@three.com",
                    "body": "Body Three"
                },
            ]
        )


class TestCommand(TestCase):

    @classmethod
    def setUpTestData(cls):
        # This record is the same with its external item
        Post.objects.create(id=1, user_id=1, title="Title One", body="Body One")

        # This record's external item needs to be updated
        Post.objects.create(id=2, user_id=2, title="Updated Title Two", body="Body Two")

        # A new external item, needs to be created for this record
        Post.objects.create(id=4, user_id=4, title="Title Four", body="Body Four")

        # This record is the same with its external item
        Comment.objects.create(post_id=1, id=1, name="Name One", email="email@one.com", body="Body One")

        # This record's external item needs to be updated
        Comment.objects.create(post_id=2, id=2, name="Updated Name Two", email="email@two.com", body="Body Two")

        # A new external item, needs to be created for this record
        Comment.objects.create(post_id=4, id=4, name="Name Four", email="email@four.com", body="Body Four")

    @mock.patch('blog.management.commands.synchronize.requests.get', fake_requests_get)
    @mock.patch('blog.management.commands.synchronize.aiohttp.ClientSession.post')
    @mock.patch('blog.management.commands.synchronize.aiohttp.ClientSession.patch')
    @mock.patch('blog.management.commands.synchronize.aiohttp.ClientSession.delete')
    def test_handle_success(
            self,
            mock_aiohttp_delete: mock.Mock,
            mock_aiohttp_patch: mock.Mock,
            mock_aiohttp_post: mock.Mock,
    ):
        """
        Fetches three records for each model (`Post` & `Comment`) from external API

        For each model, When fetches data there are three records:
            1- No change
            2- Needs update
            3- Needs delete

        Also, there is a new record in local DB, which does not exist in external DB,
        so one create (http POST) request is also needed.
        """
        mock_aiohttp_delete.return_value.__aenter__.return_value.status = 200
        mock_aiohttp_patch.return_value.__aenter__.return_value.status = 200
        mock_aiohttp_post.return_value.__aenter__.return_value.status = 201

        command = Command()
        command.handle()

        # Assert two create requests
        self.assertEqual(mock_aiohttp_post.call_count, 2)

        # Assert two update requests
        self.assertEqual(mock_aiohttp_patch.call_count, 2)

        # Assert two delete requests
        self.assertEqual(mock_aiohttp_delete.call_count, 2)

    @mock.patch('blog.management.commands.synchronize.requests.get')
    @mock.patch('blog.management.commands.synchronize.aiohttp.ClientSession.post')
    @mock.patch('blog.management.commands.synchronize.aiohttp.ClientSession.patch')
    @mock.patch('blog.management.commands.synchronize.aiohttp.ClientSession.delete')
    def test_handle_failure_get_request(
            self,
            mock_aiohttp_delete: mock.Mock,
            mock_aiohttp_patch: mock.Mock,
            mock_aiohttp_post: mock.Mock,
            mock_requests_get: mock.Mock
    ):
        mock_requests_get.side_effect = Timeout()
        mock_aiohttp_delete.return_value.__aenter__.return_value.status = 200
        mock_aiohttp_patch.return_value.__aenter__.return_value.status = 200
        mock_aiohttp_post.return_value.__aenter__.return_value.status = 201

        command = Command()
        with self.assertRaises(Timeout):
            command.handle()

        mock_aiohttp_delete.assert_not_called()
        mock_aiohttp_patch.assert_not_called()
        mock_aiohttp_post.assert_not_called()

    @mock.patch('blog.management.commands.synchronize.requests.get', fake_requests_get)
    @mock.patch('blog.management.commands.synchronize.aiohttp.ClientSession.post')
    @mock.patch('blog.management.commands.synchronize.aiohttp.ClientSession.patch')
    @mock.patch('blog.management.commands.synchronize.aiohttp.ClientSession.delete')
    def test_handle_failure_post_request(
            self,
            mock_aiohttp_delete: mock.Mock,
            mock_aiohttp_patch: mock.Mock,
            mock_aiohttp_post: mock.Mock,
    ):
        mock_aiohttp_post.side_effect = Exception()
        mock_aiohttp_delete.return_value.__aenter__.return_value.status = 200
        mock_aiohttp_patch.return_value.__aenter__.return_value.status = 200

        command = Command()
        with self.assertRaises(Exception):
            command.handle()

        self.assertEqual(mock_aiohttp_post.call_count, 1)
        self.assertEqual(mock_aiohttp_patch.call_count, 1)
        self.assertEqual(mock_aiohttp_delete.call_count, 1)
