from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
from django.conf import settings

User = get_user_model()


class UserModelTests(TestCase):
    def test_create_user_with_telefono(self):
        user = User.objects.create_user(
            email='testuser@anime.local',
            username='otaku_test',
            password='TestPassword123!',
            telefono='5511223344'
        )
        self.assertEqual(user.email, 'testuser@anime.local')
        self.assertEqual(user.username, 'otaku_test')
        self.assertEqual(user.telefono, '5511223344')
        self.assertTrue(user.check_password('TestPassword123!'))

    def test_createsuperuser_works(self):
        admin = User.objects.create_superuser(
            email='superadmin@anime.local',
            username='admin_otaku',
            password='AdminPassword123!',
            telefono='5599887766'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(admin.telefono, '5599887766')


class SecurityAndFixesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            email='admin@anime.local',
            username='admin_user',
            password='AdminPassword123!',
            telefono='5500000001'
        )
        self.victim_user = User.objects.create_user(
            email='victim@anime.local',
            username='victim_user',
            password='VictimOriginalPassword123!',
            telefono='5500000002'
        )

    def test_password_hash_never_exposed_in_auth_me(self):
        """
        FALLA CORREGIDA 1:
        Verificar que el hash de la contraseña jamás aparece en /api/v1/auth/me/.
        """
        self.client.force_authenticate(user=self.victim_user)
        response = self.client.get('/api/v1/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('password', response.data)
        self.assertEqual(response.data['email'], self.victim_user.email)
        self.assertEqual(response.data['telefono'], '5500000002')

    def test_password_hash_never_exposed_in_users_list_and_detail(self):
        """
        FALLA CORREGIDA 1:
        Verificar que el hash de la contraseña jamás aparece en el CRUD de usuarios.
        """
        self.client.force_authenticate(user=self.admin)
        # List
        res_list = self.client.get('/api/v1/users/')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        for user_data in res_list.data:
            self.assertNotIn('password', user_data)
            self.assertIn('telefono', user_data)

        # Detail
        res_detail = self.client.get(f'/api/v1/users/{self.victim_user.id}/')
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        self.assertNotIn('password', res_detail.data)
        self.assertIn('telefono', res_detail.data)

    def test_update_user_without_password_does_not_assign_requester_password(self):
        """
        FALLA CORREGIDA 2:
        En el manual, actualizar un usuario sin enviar password le asignaba la contraseña
        del usuario que realizaba la petición (request.user.password).
        Aquí comprobamos que:
        1. La contraseña del usuario víctima NO cambia.
        2. La víctima NO puede loguearse con la contraseña del admin.
        3. La víctima sigue pudiendo loguearse con su contraseña original.
        """
        self.client.force_authenticate(user=self.admin)

        # Actualizamos solo first_name y telefono sin enviar password
        payload = {
            'first_name': 'VictimUpdated',
            'telefono': '5599999999'
        }
        response = self.client.patch(f'/api/v1/users/{self.victim_user.id}/', payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('password', response.data)

        # Refrescamos el usuario de la base de datos
        self.victim_user.refresh_from_db()
        self.assertEqual(self.victim_user.first_name, 'VictimUpdated')
        self.assertEqual(self.victim_user.telefono, '5599999999')

        # Comprobar que NO tiene la contraseña del admin
        self.assertFalse(self.victim_user.check_password('AdminPassword123!'))
        # Comprobar que SIGUE teniendo su contraseña original
        self.assertTrue(self.victim_user.check_password('VictimOriginalPassword123!'))

    def test_update_user_with_new_password_changes_it_properly(self):
        """
        Cuando se envía 'password' en la petición de actualización, sí debe actualizarse.
        """
        self.client.force_authenticate(user=self.admin)
        payload = {
            'password': 'BrandNewPassword456!'
        }
        response = self.client.patch(f'/api/v1/users/{self.victim_user.id}/', payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('password', response.data)

        self.victim_user.refresh_from_db()
        self.assertTrue(self.victim_user.check_password('BrandNewPassword456!'))
        self.assertFalse(self.victim_user.check_password('VictimOriginalPassword123!'))

    def test_regular_user_cannot_escalate_to_staff_via_auth_me(self):
        """
        VULNERABILIDAD CORREGIDA (MASS ASSIGNMENT / ESCALADA DE PRIVILEGIOS):
        Verificar que un usuario común autenticado NO puede auto-promoverse a 'is_staff = True'
        ni deshabilitar su cuenta 'is_active = False' enviando atributos restringidos a /auth/me/.
        """
        self.client.force_authenticate(user=self.victim_user)
        self.assertFalse(self.victim_user.is_staff)
        self.assertTrue(self.victim_user.is_active)

        # Intento de explotación maliciosa
        payload = {
            'is_staff': True,
            'is_active': False,
            'telefono': '5511998877'
        }
        response = self.client.patch('/api/v1/auth/me/', payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # El campo permitido sí debe actualizarse
        self.assertEqual(response.data.get('telefono'), '5511998877')

        # Refrescar desde DB y verificar que las banderas sensibles NO cambiaron
        self.victim_user.refresh_from_db()
        self.assertFalse(self.victim_user.is_staff, "Falla crítica: el usuario logró auto-promoverse a staff.")
        self.assertTrue(self.victim_user.is_active, "Falla: el usuario logró mutar is_active.")
        self.assertEqual(self.victim_user.telefono, '5511998877')

        # Comprobar que sigue sin tener acceso a endpoints de administración
        res_admin = self.client.get('/api/v1/users/')
        self.assertEqual(res_admin.status_code, status.HTTP_403_FORBIDDEN)


class AuthAndTokenLifetimeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='jwttest@anime.local',
            username='jwttest',
            password='JwtPassword123!',
            telefono='5544332211'
        )

    def test_token_obtain_pair_success(self):
        """
        Comprobar que el endpoint /api/v1/auth/token/ genera tokens válidos usando email.
        """
        response = self.client.post('/api/v1/auth/token/', {
            'email': 'jwttest@anime.local',
            'password': 'JwtPassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_access_token_lifetime_configured(self):
        """
        Comprobar que ACCESS_TOKEN_LIFETIME está configurado en settings.
        """
        self.assertIn('SIMPLE_JWT', dir(settings))
        lifetime = settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME')
        self.assertIsNotNone(lifetime)
        self.assertIsInstance(lifetime, timedelta)
        self.assertEqual(lifetime, timedelta(hours=2))

    def test_throttling_configured_for_rate_limiting(self):
        """
        FALLA CORREGIDA:
        Comprobar que DEFAULT_THROTTLE_CLASSES y DEFAULT_THROTTLE_RATES están configurados
        para proteger los endpoints de autenticación y API frente a fuerza bruta.
        """
        drf_settings = getattr(settings, 'REST_FRAMEWORK', {})
        throttle_classes = drf_settings.get('DEFAULT_THROTTLE_CLASSES', ())
        throttle_rates = drf_settings.get('DEFAULT_THROTTLE_RATES', {})

        self.assertTrue(len(throttle_classes) > 0, "No se configuraron clases de Throttling.")
        self.assertIn('auth', throttle_rates, "Falta la tasa 'auth' para limitar fuerza bruta.")
        self.assertIn('anon', throttle_rates, "Falta la tasa 'anon'.")


class RegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_new_user_success(self):
        """
        Comprobar registro público con campo extra teléfono y contraseña protegida.
        """
        payload = {
            'username': 'nuevo_otaku',
            'email': 'nuevo@anime.local',
            'password': 'SecurePassword123!',
            'password_confirm': 'SecurePassword123!',
            'telefono': '5512344321'
        }
        response = self.client.post('/api/v1/auth/register/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('password', response.data)
        if 'user' in response.data:
            self.assertNotIn('password', response.data['user'])
            self.assertEqual(response.data['user']['telefono'], '5512344321')

        user = User.objects.get(email='nuevo@anime.local')
        self.assertEqual(user.username, 'nuevo_otaku')
        self.assertEqual(user.telefono, '5512344321')
        self.assertTrue(user.check_password('SecurePassword123!'))

    def test_register_short_password_fails(self):
        payload = {
            'username': 'otaku_short',
            'email': 'short@anime.local',
            'password': '123',
            'password_confirm': '123'
        }
        response = self.client.post('/api/v1/auth/register/', payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_users_with_same_email_prefix_avoids_unique_collision(self):
        """
        FALLA CORREGIDA 3:
        Verificar que si dos usuarios se registran sin especificar username pero comparten
        el mismo prefijo de correo (ej. otaku_fan@dominio1.com y otaku_fan@dominio2.com),
        la base de datos NO arroja un IntegrityError (HTTP 500) y asigna un identificador único.
        """
        res1 = self.client.post('/api/v1/auth/register/', {
            'email': 'otaku_fan@dominio1.local',
            'password': 'Password123!',
            'password_confirm': 'Password123!',
        })
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        res2 = self.client.post('/api/v1/auth/register/', {
            'email': 'otaku_fan@dominio2.local',
            'password': 'Password456!',
            'password_confirm': 'Password456!',
        })
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)

        u1 = User.objects.get(email='otaku_fan@dominio1.local')
        u2 = User.objects.get(email='otaku_fan@dominio2.local')
        self.assertEqual(u1.username, 'otaku_fan')
        self.assertEqual(u2.username, 'otaku_fan_1')
        self.assertNotEqual(u1.username, u2.username)


class SwaggerDocumentationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_swagger_schema_json_contains_anime_title(self):
        """
        Comprobar que el título de Swagger NO es 'restaurante' y es acorde al proyecto 'Anime Recommended API',
        y que incluye el campo extra 'telefono' en los esquemas.
        """
        response = self.client.get('/swagger/?format=openapi')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode('utf-8')
        self.assertIn('Anime Recommended API', content)
        self.assertNotIn('restaurante', content.lower())
        self.assertIn('telefono', content)
