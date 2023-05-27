from rest_framework import routers
from django.urls import reverse
from django.urls import get_resolver

from blog.api.v1.post.views import PostView
from blog.api.v1.comment.views import CommentView

router = routers.SimpleRouter()
router.register(r'posts', PostView)
router.register(r'comments', CommentView)
urlpatterns = router.urls
