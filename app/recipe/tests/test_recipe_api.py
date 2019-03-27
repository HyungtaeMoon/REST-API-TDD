from django.contrib.auth import get_user_model
# TestCase 는 transaction 테스트 케이스로 모든 작업이 끝났을 때 갱신이 됨
# 중간에 오류가 발생했을 경우에는 그 전에 했던 작업들도 모두 기본 초기화
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe
from recipe.serializer import RecipeSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def sample_recipe(user, **params):
    """sample recipe 객체를 생성, 리턴"""
    defaults = {
        'title': 'sample recipe',
        'time_minutes': 10,
        'price': 5.00,
    }
    # dict 의 메서드인 update 사용
    # 여러개의 데이터를 한꺼번에 갱신하는데 유용한 메서드
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """인증받지 않은 recipe API 가 접근했을 경우의 테스트"""
    def setUp(self):
        self.client = APIClient()

    def test_required_auth(self):
        """인증 테스트로 status 401 을 리턴 받아야 함"""
        res = self.client.get(RECIPES_URL)

        self.assertTrue(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """인증된 유저의 recipe API 테스트"""
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@master.com',
            'pass1234'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """recipe 검색 테스트"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """인증 된 유저만 결과값을 반환하는지 테스트"""
        user2 = get_user_model().objects.create_user(
            'other@master.com',
            'pass4321'
        )
        # user2 는 인증받지 못한 유저 객체
        sample_recipe(user=user2)
        # self.user 는 setUp 에서 force_authenticate 를 받았음
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        # RecipeSerializer 와 비교하기 위해 쿼리셋을 반환하는 filter 를 사용
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)
