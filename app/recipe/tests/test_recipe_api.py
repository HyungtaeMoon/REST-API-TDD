from django.contrib.auth import get_user_model
# TestCase 는 transaction 테스트 케이스로 모든 작업이 끝났을 때 갱신이 됨
# 중간에 오류가 발생했을 경우에는 그 전에 했던 작업들도 모두 기본 초기화
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializer import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def sample_tag(user, name='Main course'):
    """태그 객체 생성"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Cinnammon'):
    """성분 객체 생성"""
    return Ingredient.objects.create(user=user, name=name)


def detail_url(recipe_id):
    """recipe detail URL 을 리턴"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


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

    def test_view_recipe_detail(self):
        """recipe 세부 사항 보기 테스트"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        # api/recipe/recipes/6/
        url = detail_url(recipe.id)
        res = self.client.get(url)

        # 단일 객체를 받기 때문에 many=True 옵션은 지정하지 않음
        # serializer 는 데이터를 사전으로 변환
        # return 되는 OrderedDict 는 순서를 기억하는 사전형
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """recipe 생성 테스트"""
        payload = {
            'title': 'Cheese cake',
            'time_minutes': 30,
            'price': 10.00,
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        # recipe 객체에 payload 의 key 값이 있는지 확인
        for key in payload.keys():
            # 변수를 전달하여 속성에 접근 recipe.key 는 검색이 되지 않음
            # recipe.title, recipe.time_minutes, recipe.price 를 순차 검색
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """tags 를 포함한 recipe 생성 테스트"""
        tags1 = sample_tag(user=self.user, name='Sweet')
        tags2 = sample_tag(user=self.user, name='Desert')
        # 현재 모델 관계에서는 tags 의 객체는 400 에러를 발생, tags.id 로 참조해야 함
        payload = {
            'title': 'Chocolate Strawberry Cake',
            'tags': [tags1.id, tags2.id],
            'time_minutes': 30,
            'price': 10.00,
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        # Many-To-Many 필드 관계이며, 해당 recipe 를 참조한 tag 객체를 모두 불러옴
        tags = recipe.tags.all()
        # tags1, tags2 객체 2개가 존재하는지 확인
        self.assertEqual(tags.count(), 2)
        # tags 안에 멤버십으로 tags1, tags2 가 포함되는지 확인
        self.assertIn(tags1, tags)
        self.assertIn(tags2, tags)

    def test_create_recipe_with_ingredients(self):
        """ingredients 를 포함한 recipe 생성 테스트"""
        ingredient1 = sample_ingredient(user=self.user, name='Carrot')
        ingredient2 = sample_ingredient(user=self.user, name='Potato')
        payload = {
            'title': 'Korean Style Curry',
            'ingredients': [ingredient1.id, ingredient2.id],
            'time_minutes': 30,
            'price': 10.00,
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)
