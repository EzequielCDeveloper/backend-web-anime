from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class AnimeReview(models.Model):
    """
    Modelo para persistir valoraciones y reseñas comunitarias de animes.
    Garantiza que un usuario solo pueda emitir una valoración por anime (unique constraint).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='anime_reviews',
        verbose_name="Usuario"
    )
    anime_id = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name="ID de Anime (Kitsu)",
        help_text="Identificador único del anime en la API externa de Kitsu"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="Puntuación (1-10)",
        help_text="Calificación del anime del 1 al 10"
    )
    comment = models.TextField(
        blank=True,
        verbose_name="Comentario o Reseña",
        help_text="Opinión o reseña textual de la obra"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización"
    )

    class Meta:
        verbose_name = "Valoración y Reseña de Anime"
        verbose_name_plural = "Valoraciones y Reseñas de Anime"
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'anime_id'],
                name='unique_user_anime_review'
            )
        ]

    def __str__(self):
        return f"{self.user.email} -> Anime #{self.anime_id} ({self.rating}/10)"
