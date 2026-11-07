# Anime Recommended - Backend (Django REST Framework)

Backend para la plataforma de recomendación de anime (**Anime Recommended**). Desarrollado con Django, Django REST Framework, autenticación JWT (SimpleJWT) y documentación interactiva con Swagger / OpenAPI (`drf-yasg`).

---

## 🚀 Requisitos e Instalación

### 1. Activar entorno virtual
```bash
cd backend
source venv/bin/activate
```

### 2. Instalar dependencias (si configuras un nuevo entorno)
```bash
pip install -r requirements.txt
```

### 3. Migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Iniciar el servidor
```bash
python manage.py runserver
```
El backend estará disponible en `http://127.0.0.1:8000/`.

---

## 🔑 Credenciales de Prueba

- **Superadministrador (Django Admin / Swagger):**
  - **Email:** `admin@animerecommended.com`
  - **Contraseña:** `Admin1234!`
  - **Teléfono:** `5512345678`

- **Usuario Regular (VIP Demo):**
  - **Email:** `usuario_vip@selectanime.com`
  - **Contraseña:** `Anime1234!`
  - **Teléfono:** `5587654321`

---

## 📖 Documentación Interactiva de la API

- **Swagger UI:** `http://127.0.0.1:8000/swagger/`
- **ReDoc:** `http://127.0.0.1:8000/redoc/`
- **OpenAPI Schema (JSON):** `http://127.0.0.1:8000/swagger/?format=openapi`

---

## 🛡️ Correcciones de Seguridad Implementadas

1. **Exposición de hashes de contraseñas eliminada:**
   - La contraseña se configuró como `write_only=True` en los serializadores y se remueve defensivamente en `to_representation()`.
   - Jamás se devuelve el hash en `GET /api/v1/auth/me/`, `GET /api/v1/users/` ni en ningún endpoint.

2. **Error al actualizar usuario sin contraseña corregido:**
   - En el manual, actualizar un usuario sin enviar `password` le asignaba `request.user.password` (la contraseña de quien hacía la petición).
   - Se corrigió en el `UserSerializer` y en `UserApiViewSet` para que la contraseña existente del usuario permanezca intacta a menos que se envíe explícitamente una nueva contraseña.

---

## ⏱️ Configuración de Tokens JWT

En `anime_backend/settings.py`:
- `ACCESS_TOKEN_LIFETIME = timedelta(hours=2)`
- `REFRESH_TOKEN_LIFETIME = timedelta(days=7)`

---

## 🧪 Pruebas Unitarias

Ejecutar la suite completa de pruebas:
```bash
python manage.py test users
```
