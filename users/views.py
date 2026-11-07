from django.shortcuts import render
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_yasg.utils import swagger_auto_schema

from users.models import User
from users.serializers import UserSerializer, UserProfileSerializer, RegisterUserSerializer


class ThrottledTokenObtainPairView(TokenObtainPairView):
    """
    Endpoint para autenticación con tokens JWT protegido por limitación de tasa (Rate Limiting).
    Mitiga ataques de fuerza bruta y credential stuffing sobre las credenciales de los usuarios.
    """
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'


class UserApiViewSet(ModelViewSet):
    """
    CRUD completo de usuarios administrable exclusivamente por usuarios Staff / Admin.
    
    CORRECCIÓN DE SEGURIDAD DEL MANUAL:
    1. Nunca expone el hash de contraseñas en las respuestas (controlado en UserSerializer).
    2. Al actualizar mediante PUT o PATCH sin enviar 'password', la contraseña del usuario
       a modificar permanece intacta. El código erróneo del manual asignaba `request.user.password`,
       lo que sobrescribía la contraseña de la víctima con la del usuario que realizaba la petición.
    """
    permission_classes = [IsAdminUser]
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def partial_update(self, request, *args, **kwargs):
        """
        Actualización parcial segura (PATCH).
        Si no se envía 'password', se actualizan los demás campos sin alterar la contraseña.
        Si se envía 'password', el UserSerializer aplica `set_password` de forma segura.
        """
        return super().partial_update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        Actualización total segura (PUT).
        """
        return super().update(request, *args, **kwargs)


class UserView(APIView):
    """
    Endpoint para consultar y actualizar los datos del usuario autenticado (auth/me/).
    
    CORRECCIÓN DE SEGURIDAD (MASS ASSIGNMENT & ESCALADA DE PRIVILEGIOS - CWE-915):
    Utiliza UserProfileSerializer, blindando 'is_staff' e 'is_active' como campos de solo lectura,
    e impidiendo que usuarios comunes eleven sus privilegios en la aplicación.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Obtiene los datos del perfil del usuario actualmente autenticado.",
        responses={200: UserProfileSerializer}
    )
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Actualiza los datos del perfil del usuario actualmente autenticado.",
        request_body=UserProfileSerializer,
        responses={200: UserProfileSerializer}
    )
    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterUserView(ModelViewSet):
    """
    Endpoint público para el registro de nuevos usuarios en la plataforma.
    Solo permite el método POST para evitar listar usuarios a personas no autorizadas.
    Protegido con Rate Limiting para evitar inundación de registros automatizados.
    """
    permission_classes = [AllowAny]
    serializer_class = RegisterUserSerializer
    queryset = User.objects.all()
    http_method_names = ['post', 'head', 'options']
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    @swagger_auto_schema(
        operation_description="Registra una nueva cuenta de usuario en la plataforma.",
        request_body=RegisterUserSerializer,
        responses={
            201: "Usuario registrado exitosamente",
            400: "Datos inválidos o contraseñas no coincidentes"
        }
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'status': 'success',
                'message': 'Usuario registrado exitosamente',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'telefono': user.telefono,
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
