from django.db.models import Avg
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from reviews.models import AnimeReview
from reviews.serializers import AnimeReviewSerializer
from reviews.permissions import IsAuthorOrReadOnly


class AnimeReviewViewSet(viewsets.ModelViewSet):
    """
    CRUD completo y optimizado para Valoraciones y Reseñas comunitarias de Anime.
    Soporta cálculo agregado de calificación promedio y detección del estado del usuario.
    """
    queryset = AnimeReview.objects.select_related('user').all()
    serializer_class = AnimeReviewSerializer
    permission_classes = [IsAuthorOrReadOnly]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'reviews'
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        if self.action in ['create']:
            return [IsAuthenticated()]
        return [IsAuthorOrReadOnly()]

    @swagger_auto_schema(
        operation_description="Lista las reseñas de un anime, calcula el promedio y retorna la valoración del usuario en sesión.",
        manual_parameters=[
            openapi.Parameter(
                'anime_id',
                openapi.IN_QUERY,
                description="ID del anime de Kitsu para filtrar",
                type=openapi.TYPE_STRING,
                required=False
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        anime_id = request.query_params.get('anime_id')
        queryset = self.get_queryset()

        if anime_id:
            queryset = queryset.filter(anime_id=anime_id)
            avg_result = queryset.aggregate(avg=Avg('rating'))['avg']
            average_rating = round(avg_result, 1) if avg_result is not None else None

            user_review_data = None
            if request.user.is_authenticated:
                user_review = queryset.filter(user=request.user).first()
                if user_review:
                    user_review_data = self.get_serializer(user_review).data

            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'anime_id': anime_id,
                'count': queryset.count(),
                'average_rating': average_rating,
                'user_review': user_review_data,
                'reviews': serializer.data,
            })

        serializer = self.get_serializer(queryset[:50], many=True)
        return Response({
            'count': queryset.count(),
            'reviews': serializer.data,
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response(
            self.get_serializer(review).data,
            status=status.HTTP_201_CREATED
        )
