'''Test for Ingredient API.'''

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import (
    Recipe,
    Tag,
    Ingredient,
)

from recipe.serializers import IngredientSerializer


INGREDIENT_URL = reverse('recipe:ingredient-list')


def detail_url(ingredient_id):
    '''Create and return an ingredient detail URL.'''
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(email='user@example.com', password='password123'):
    '''Create and return a new user.'''
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientAPITest(TestCase):
    '''Test unauthenticated API requests.'''

    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self):
        '''Test auth is required for retriving ingredients.'''
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientAPITest(TestCase):
    '''Test authenticated API requests.'''

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrive_list_of_ingredients(self):
        '''Test retreving a lis of ingredients.'''
        Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='vanilla')

        res = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retive_ingredient_limit_to_user(self):
        '''Test retrive ingredient to authenticated user.'''
        user2 = create_user(email='user2@example.com', password='password123')

        ingredient = Ingredient.objects.create(user=self.user, name='Pepper')
        Ingredient.objects.create(user=user2, name='Salt')

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_update_ingredient(self):
        '''Test updating an ingredient.'''
        ingredient = Ingredient.objects.create(user=self.user, name='Pepper')
        payload = {'name': 'Salt'}
        url = detail_url(ingredient.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        '''Test deleting an ingredient.'''
        ingredient = Ingredient.objects.create(user=self.user, name='Pepper')
        url = detail_url(ingredient.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())
