from django.contrib import admin

from blog.models.post import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'user_id']
