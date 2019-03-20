from django.test import TestCase

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient
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
