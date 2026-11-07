from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from reviews.models import AnimeReview

User = get_user_model()


class AnimeReviewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            email='reviewer1@anime.local',
            username='reviewer_one',
            password='Password123!'
        )
        self.user2 = User.objects.create_user(
            email='reviewer2@anime.local',
            username='reviewer_two',
            password='Password123!'
        )

    def test_anonymous_user_can_read_reviews_and_average(self):
        # Creamos dos reseñas para el anime 42
        AnimeReview.objects.create(user=self.user1, anime_id='42', rating=8, comment="Muy bueno")
        AnimeReview.objects.create(user=self.user2, anime_id='42', rating=10, comment="Obra de arte")

        response = self.client.get('/api/v1/reviews/?anime_id=42')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['anime_id'], '42')
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['average_rating'], 9.0)
        self.assertIsNone(response.data['user_review'])
        self.assertEqual(len(response.data['reviews']), 2)

    def test_authenticated_user_sees_their_own_review_hydrated(self):
        AnimeReview.objects.create(user=self.user1, anime_id='100', rating=6, comment="Regular")

        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/api/v1/reviews/?anime_id=100')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['user_review'])
        self.assertEqual(response.data['user_review']['rating'], 6)
        self.assertTrue(response.data['reviews'][0]['is_author'])

    def test_create_review_authenticated(self):
        self.client.force_authenticate(user=self.user1)
        payload = {
            'anime_id': '15',
            'rating': 9,
            'comment': 'Excelente animación de batalla.'
        }
        response = self.client.post('/api/v1/reviews/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['rating'], 9)
        self.assertEqual(response.data['anime_id'], '15')
        self.assertEqual(response.data['username'], 'reviewer_one')

        self.assertEqual(AnimeReview.objects.filter(anime_id='15').count(), 1)

    def test_unauthenticated_user_cannot_create_review(self):
        payload = {'anime_id': '15', 'rating': 8, 'comment': 'Intento anónimo'}
        response = self.client.post('/api/v1/reviews/', payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_upsert_review_updates_existing_rating(self):
        self.client.force_authenticate(user=self.user1)
        # Primera calificación
        self.client.post('/api/v1/reviews/', {'anime_id': '20', 'rating': 5, 'comment': 'Primera impresión'})
        self.assertEqual(AnimeReview.objects.filter(user=self.user1, anime_id='20').count(), 1)

        # Segunda calificación (debe actualizar, no duplicar ni dar IntegrityError)
        res = self.client.post('/api/v1/reviews/', {'anime_id': '20', 'rating': 9, 'comment': 'Mejoró al final'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['rating'], 9)
        self.assertEqual(res.data['comment'], 'Mejoró al final')

        # Se mantiene exactamente un solo registro en base de datos
        self.assertEqual(AnimeReview.objects.filter(user=self.user1, anime_id='20').count(), 1)

    def test_user_cannot_delete_another_users_review(self):
        review = AnimeReview.objects.create(user=self.user1, anime_id='30', rating=8)

        # Usuario 2 intenta borrar la reseña del Usuario 1
        self.client.force_authenticate(user=self.user2)
        response = self.client.delete(f'/api/v1/reviews/{review.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(AnimeReview.objects.filter(id=review.id).exists())

    def test_author_can_delete_their_own_review(self):
        review = AnimeReview.objects.create(user=self.user1, anime_id='30', rating=8)

        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(f'/api/v1/reviews/{review.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(AnimeReview.objects.filter(id=review.id).exists())

    def test_invalid_rating_value_fails(self):
        self.client.force_authenticate(user=self.user1)
        res_low = self.client.post('/api/v1/reviews/', {'anime_id': '50', 'rating': 0})
        self.assertEqual(res_low.status_code, status.HTTP_400_BAD_REQUEST)

        res_high = self.client.post('/api/v1/reviews/', {'anime_id': '50', 'rating': 11})
        self.assertEqual(res_high.status_code, status.HTTP_400_BAD_REQUEST)
