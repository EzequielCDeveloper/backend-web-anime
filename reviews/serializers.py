from rest_framework import serializers
from reviews.models import AnimeReview


class AnimeReviewSerializer(serializers.ModelSerializer):
    """
    Serializer para lectura, creación y actualización de reseñas y calificaciones.
    Asigna automáticamente el usuario autenticado desde el contexto de la petición
    y realiza upsert automático para garantizar unicidad sin errores 500.
    """
    username = serializers.SerializerMethodField(read_only=True)
    is_author = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AnimeReview
        fields = [
            'id',
            'anime_id',
            'rating',
            'comment',
            'username',
            'is_author',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'username', 'is_author', 'created_at', 'updated_at']

    def get_username(self, obj):
        return obj.user.username or obj.user.email.split('@')[0]

    def get_is_author(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user_id == request.user.id
        return False

    def validate_rating(self, value):
        if value < 1 or value > 10:
            raise serializers.ValidationError("La puntuación debe estar entre 1 y 10.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        anime_id = validated_data['anime_id']
        rating = validated_data['rating']
        comment = validated_data.get('comment', '')

        # Upsert atómico: actualiza si ya existe la reseña del usuario para este anime
        review, _ = AnimeReview.objects.update_or_create(
            user=user,
            anime_id=anime_id,
            defaults={
                'rating': rating,
                'comment': comment,
            }
        )
        return review
