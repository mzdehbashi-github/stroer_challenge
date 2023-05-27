from typing import Union, Type
import logging
import asyncio

from django.core.management.base import BaseCommand
import requests
import aiohttp

from blog.models.post import Post
from blog.models.comment import Comment

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def send_patch_request(session: aiohttp.ClientSession, url: str, data: dict):
    """
    Send a PATCH request to the specified URL with the provided data using the given session.
    """
    async with session.patch(url, json=data) as response:
        if response.status != 200:
            logger.warning(f'Update request to {url=} with {data=} got {response.status=}')
        else:
            logger.info(f'Update request to {url=} succeeded')


async def send_delete_request(session: aiohttp.ClientSession, url: str):
    """
    Send a DELETE request to the specified URL using the given session.
    """
    async with session.delete(url) as response:
        if response.status != 200:
            logger.warning(f'Delete request to {url=} got {response.status=}')
        else:
            logger.info(f'Delete request to {url=} succeeded')


async def process_update_and_delete(
        model_class: Union[Type[Post], Type[Comment]],
        external_items,
        internal_items
):
    """
    Process update and delete operations for the specified model class using the provided external
    and internal items.
    """
    tasks = []
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
        for external_item in external_items:
            item_id = external_item['id']
            if internal_item := internal_items.get(item_id):
                # Check to see if there is a diff
                for key, value in internal_item.serialized_value.items():
                    if external_item[key] != value:  # If `True` then there is a diff
                        task = asyncio.ensure_future(
                            send_patch_request(
                                session=session,
                                url=internal_item.update_delete_url(item_id),
                                data=internal_item.serialized_value
                            )
                        )

                        tasks.append(task)
                        break

            else:
                # Mean item exist in external DB but not in internal DB, so it should be also deleted
                # from the external DB
                tasks.append(
                    asyncio.ensure_future(
                        send_delete_request(session, model_class.update_delete_url(item_id))
                    )
                )

        await asyncio.gather(*tasks)


async def send_post_request(session, url, data):
    """
    Send a POST request to the specified URL with the provided data using the given session.
    """
    async with session.post(url, json=data) as response:

        if response.status != 201:
            logger.warning(f'Create request to {url=} with {data=} got {response.status=}')
        else:
            logger.info(f'Create request to {url=} succeeded')


async def process_create_items(items):
    """
    Process create operations for the specified items.
    """
    tasks = []
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
        for item in items:
            data = item.serialized_value
            url = item.list_create_url()
            tasks.append(
                asyncio.ensure_future(
                    send_post_request(session, url, data)
                )
            )

        await asyncio.gather(*tasks)


class Command(BaseCommand):

    def handle(self, *args, **options):
        for model_class in (Post, Comment):
            # Get the external items

            # Here we can also fetch items from external resource by pagination
            # To prevent loading all items into memory at once.
            external_posts_response = requests.get(model_class.list_create_url())
            external_items_json = external_posts_response.json()
            external_items_ids = [external_post['id'] for external_post in external_items_json]

            # Get the internal items
            internal_items = model_class.objects.filter(id__in=external_items_ids)
            internal_items_by_id = {
                internal_post.id: internal_post for internal_post in internal_items
            }

            # Process update and delete operations
            asyncio.run(
                process_update_and_delete(
                    model_class=model_class,
                    external_items=external_items_json,
                    internal_items=internal_items_by_id,
                )
            )

            # After processing all update|delete operations (with or without pagination)
            # Now we know fo sure, that which items (IDs), exist in external DB,
            # So by performing `exclude` query, we can find that which items needed
            # to be created in the external DB.
            # To prevent loading all items in memory, We can also fetch new items from DB, in chunks.

            # Get new items that need to be created
            new_items = model_class.objects.exclude(id__in=external_items_ids)

            # Process create operations
            asyncio.run(process_create_items(list(new_items)))
