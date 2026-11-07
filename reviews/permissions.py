from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado que permite lectura a cualquiera (GET, HEAD, OPTIONS),
    pero solo permite modificar o eliminar (PUT, PATCH, DELETE) al autor de la reseña
    o a un administrador del sistema.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user or bool(request.user and request.user.is_staff)
