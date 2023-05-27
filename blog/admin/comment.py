from django.contrib import admin

from blog.models.comment import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['post_title', 'email']
    list_select_related = ['post']

    @admin.display
    def post_title(self, comment: Comment) -> str:
        return comment.post.title
