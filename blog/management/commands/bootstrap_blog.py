from itertools import islice
from typing import List
import asyncio
import io

from django.db import connection
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import transaction
from django.conf import settings
import requests
import aiohttp

from blog.models.post import Post
from blog.models.comment import Comment


def chunk_list(lst, chunk_size):
    it = iter(lst)
    chunk = list(islice(it, chunk_size))
    while chunk:
        yield chunk
        chunk = list(islice(it, chunk_size))


async def fetch_json(session, url):
    async with session.get(url) as response:
        return await response.json()


async def process_item(session, post: Post) -> List[Comment]:
    url = settings.COMMENTS_BY_POST_URL.format(post.id)
    comments_data = await fetch_json(session, url)
    return [
        Comment(
            post=post,
            id=comment_data['id'],
            name=comment_data['name'],
            email=comment_data['email'],
            body=comment_data['body']
        ) for comment_data in comments_data
    ]


async def process_items(chunk: List[Post]):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
        tasks = [process_item(session, post) for post in chunk]
        results = await asyncio.gather(*tasks)
        return results


class Command(BaseCommand):

    def handle(self, *args, **options):
        # With the current amount of data, in the external API,
        # it is possible to just make two sync calls and create records in DB, using two
        # django-ORM's `bulk_create` calls (for `Post` & `Comment`)

        # But this approach might fail, if the amount of data in external API is huge,
        # We need to fetch records, in chunks (using pagination) from external API, and then
        # create them in chunks in local DB, that is the reason I chose this approach:
        # Fetch posts (in pagination if it was available in external API) in chunks, for each chunk:
        #    1- Create all posts in the local DB
        #    2- Fetch all comments for the chunk of posts (using asyncio to improve performance)
        #    3- Create all comments in local DB

        if Post.objects.exists():
            raise CommandError('Can not import records from external API, since there are existing ones in DB')

        posts_response = requests.get(settings.POSTS_URL)
        posts_data = posts_response.json()
        posts_bulk = [
            Post(
                id=post_data['id'],
                user_id=post_data['userId'],
                title=post_data['title'],
                body=post_data['body'],
            ) for post_data in posts_data
        ]

        with transaction.atomic():
            posts = Post.objects.bulk_create(posts_bulk)
            comments_bulk: List[Comment] = []
            for chunk in chunk_list(posts, chunk_size=20):
                comment_chunks: List[List[Comment]] = asyncio.run(process_items(chunk))
                for comment_chunk in comment_chunks:
                    comments_bulk.extend(comment_chunk)

            Comment.objects.bulk_create(comments_bulk)

            # Since we created records and added the IDs manually, we need to
            # sync primary keys for related tables in DB
            app_name = 'blog'
            # Get SQL commands from sqlsequencereset
            output = io.StringIO()
            call_command('sqlsequencereset', app_name, stdout=output, no_color=True)
            sql = output.getvalue()

            with connection.cursor() as cursor:
                cursor.execute(sql)

            output.close()
