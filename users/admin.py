from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Configuración personalizada del modelo User en el panel de administración de Django.
    Asegura que el campo extra 'telefono' sea visible en el listado,
    en la búsqueda, y en los formularios de adición y edición.
    """
    list_display = (
        'id',
        'email',
        'username',
        'first_name',
        'last_name',
        'telefono',
        'is_staff',
        'is_active',
        'date_joined',
    )
    list_display_links = ('id', 'email')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'telefono')
    ordering = ('-id',)

    # Formulario para editar usuario existente
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {
            'fields': ('username', 'first_name', 'last_name', 'telefono')
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Fechas Importantes', {
            'fields': ('last_login', 'date_joined')
        }),
    )

    # Formulario para crear usuario desde el Admin
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'telefono', 'password'),
        }),
    )
