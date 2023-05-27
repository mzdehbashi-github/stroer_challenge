from django.test import TransactionTestCase
from unittest.mock import patch, MagicMock

from blog.models import Post, Comment
from blog.management.commands import bootstrap_blog


class TestCommand(TransactionTestCase):

    def setUp(self):
        self.command = bootstrap_blog.Command()

        # Mock the aiohttp.ClientSession
        self.mock_client_session = patch('blog.management.commands.bootstrap_blog.aiohttp.ClientSession').start()
        self.mock_session_instance = MagicMock()
        self.mock_client_session.return_value = self.mock_session_instance

    def tearDown(self):
        # Stop the patch for aiohttp.ClientSession
        self.mock_client_session.stop()

    @patch('requests.get')
    @patch('blog.management.commands.bootstrap_blog.fetch_json')
    def test_handle_success(self, mock_fetch_json, mock_requests_get):
        # Mock the response from posts endpoint
        posts_data = [
            {'id': 1, 'userId': 1, 'title': 'Post 1', 'body': 'Body 1'},
        ]
        mock_posts_response = MagicMock()
        mock_posts_response.json.return_value = posts_data
        mock_requests_get.return_value = mock_posts_response

        # Mock the response from comments endpoint
        comments_data = [
            {'id': 1, 'name': 'Comment 1', 'email': 'comment1@example.com', 'body': 'Comment body 1'},
            {'id': 2, 'name': 'Comment 2', 'email': 'comment2@example.com', 'body': 'Comment body 2'},
        ]
        mock_fetch_json.return_value = comments_data

        # Execute the command
        self.command.handle()

        # Assertions
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(Comment.objects.count(), 2)

    @patch('requests.get')
    def test_handle_posts_request_failure(self, mock_requests_get):
        # Mock the failed response from posts endpoint
        mock_posts_response = MagicMock()
        mock_posts_response.json.side_effect = Exception('Posts endpoint error')
        mock_requests_get.return_value = mock_posts_response

        # Execute the command
        with self.assertRaises(Exception):
            self.command.handle()

        # Assertions
        self.assertEqual(Post.objects.count(), 0)
        self.assertEqual(Comment.objects.count(), 0)

    @patch('requests.get')
    @patch('blog.management.commands.bootstrap_blog.fetch_json')
    def test_handle_comments_request_failure(self, mock_fetch_json, mock_requests_get):
        # Mock the response from posts endpoint
        posts_data = [
            {'id': 1, 'userId': 1, 'title': 'Post 1', 'body': 'Body 1'},
            {'id': 2, 'userId': 2, 'title': 'Post 2', 'body': 'Body 2'},
        ]
        mock_posts_response = MagicMock()
        mock_posts_response.json.return_value = posts_data
        mock_requests_get.return_value = mock_posts_response

        # Mock the failed response from comments endpoint
        mock_fetch_json.side_effect = Exception('Comments endpoint error')

        # Execute the command
        with self.assertRaises(Exception):
            self.command.handle()

        # Assertions
        self.assertEqual(Post.objects.count(), 0)
        self.assertEqual(Comment.objects.count(), 0)

    @patch('requests.get')
    def test_handle_invalid_posts_data(self, mock_requests_get):
        # Mock the invalid response from posts endpoint
        invalid_posts_data = [
            {'userId': 1, 'title': 'Post 1', 'body': 'Body 1'},
            {'id': 2, 'userId': 2, 'title': 'Post 2', 'body': 'Body 2'},
        ]
        mock_posts_response = MagicMock()
        mock_posts_response.json.return_value = invalid_posts_data
        mock_requests_get.return_value = mock_posts_response

        # Execute the command
        with self.assertRaises(KeyError):  # Raises KeyError since the first post item does not have field 'id'
            self.command.handle()

        # Assertions
        self.assertEqual(Post.objects.count(), 0)
        self.assertEqual(Comment.objects.count(), 0)
