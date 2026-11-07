from django.contrib import admin
from reviews.models import AnimeReview


@admin.register(AnimeReview)
class AnimeReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'anime_id', 'rating', 'created_at', 'updated_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('anime_id', 'user__email', 'user__username', 'comment')
    ordering = ('-created_at',)
