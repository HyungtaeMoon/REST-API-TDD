from django.test import TestCase

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
from ..serializer import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientsApiTests(TestCase):
    """공개적으로 사용 가능한 레시피 지료의 API 테스트"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """endpoint 에 접근하려면 로그인이 필요"""
        res = self.client.get(INGREDIENTS_URL)
        # 인증되지 않은 사용자이기 때문에 401 상태코드를 받음
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsAPITests(TestCase):
    """허가 된 사용자만 검색할 수 있도록 하는 테스트"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@ingredient.com',
            'test1234'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient_list(self):
        """레시피의 성분 목록 검색 테스트"""
        Ingredient.objects.create(user=self.user, name='kale')
        Ingredient.objects.create(user=self.user, name='salt')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # ingredients 와 serializer 2개 모두 쿼리셋을 가져옴
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """인증된 유저만 결과값을 반환할 수 있는지 태그인지 테스트"""
        user2 = get_user_model().objects.create_user(
            'other@test.com',
            'pass1234'
        )
        Ingredient.objects.create(user=user2, name='Vinegar')
        ingredient = Ingredient.objects.create(user=self.user, name='tire')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        """새로 생성한 성분 테스트"""
        payload = {'name': 'Cabbage'}
        # post 요청으로 payload 를 보냄
        self.client.post(INGREDIENTS_URL, payload)

        # exists() 메서드는 쿼리셋 캐시를 만들지 않으면서 레코드가 존재하는지 검사
        # 메모리 사용은 최적화되지만 쿼리셋 캐시는 생성되지 않아 DB 쿼리가 중복될 수 있음
        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """invalid 한 payload 의 태그를 생성했을 경우의 테스트"""
        payload = {'name': ''}
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertTrue(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assigned_to_recipes(self):
        """recipe 에 지정된 ingredient 로 필터링하는 테스트"""
        ingredient1 = Ingredient.objects.create(
            user=self.user,
            name='Apples',
        )
        ingredient2 = Ingredient.objects.create(
            user=self.user,
            name='Salt',
        )
        recipe = Recipe.objects.create(
            title='Egg benedict',
            time_minutes=5,
            price=4.00,
            user=self.user,
        )
        recipe.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_ingredient_assigned_unique(self):
        """2개의 recipe 가 ingredient 1개 참조했을 때 테스트"""
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Eggs',
        )
        recipe1 = Recipe.objects.create(
            title='Scrambled eggs',
            time_minutes=4,
            price=5.00,
            user=self.user,
        )
        recipe1.ingredients.add(ingredient)
        recipe2 = Recipe.objects.create(
            title='Egg benedict',
            time_minutes=20,
            price=10.00,
            user=self.user,
        )
        recipe2.ingredients.add(ingredient)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
