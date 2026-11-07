from django.urls import path, include
from rest_framework.routers import DefaultRouter
from reviews.views import AnimeReviewViewSet

router = DefaultRouter()
router.register(r'reviews', AnimeReviewViewSet, basename='anime-reviews')

urlpatterns = [
    path('', include(router.urls)),
]
