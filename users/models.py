from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Modelo de usuario personalizado para la plataforma Anime Recommended.
    Utiliza el email como identificador principal (USERNAME_FIELD).
    Incluye campo extra 'telefono' para contacto y perfil de usuario.
    """
    email = models.EmailField(unique=True, verbose_name="Correo electrónico")
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Teléfono",
        help_text="Número de teléfono o móvil del usuario"
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['-id']

    def save(self, *args, **kwargs):
        # Asegurar que username tenga un valor por defecto único si no se proporciona
        if not self.username and self.email:
            base_username = self.email.split('@')[0]
            candidate = base_username
            counter = 1
            while User.objects.filter(username=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base_username}_{counter}"
                counter += 1
            self.username = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.email} ({self.username or 'Sin username'})"
