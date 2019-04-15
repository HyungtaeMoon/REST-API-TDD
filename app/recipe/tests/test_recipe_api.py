import os
import tempfile

from django.contrib.auth import get_user_model
# TestCase 는 transaction 테스트 케이스로 모든 작업이 끝났을 때 갱신이 됨
# 중간에 오류가 발생했을 경우에는 그 전에 했던 작업들도 모두 기본 초기화
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializer import RecipeSerializer, RecipeDetailSerializer

from PIL import Image

RECIPES_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    """recipe image upload URL 을 리턴"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def sample_tag(user, name='Main course'):
    """태그 객체 생성"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Cinnamon'):
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

    def test_one_create_tag(self):
        """
        sample_tag 함수에서 name='Main course' 로 설정.
        tag 객체를 생성할 때 name=None 이어도 이미 생성한 Main course 로 받아와지는지 테스트
        """
        tag = sample_tag(user=self.user)
        payload = {
            'user': self.user,
            'name': 'Main course',
        }
        # Main course
        # print(tag.name)
        self.assertEqual(tag.name, payload['name'])

    def test_partial_update_recipe(self):
        """
        patch 를 통한 recipe 업데이트 테스트

        patch: 자원의 일부를 수정(요청 시에 수정하고자 하는 자원만 있으면 됨)
        """
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name='Curry')

        payload = {'title': 'Chicken Stew', 'tags': new_tag.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        # refresh_from_db() 함수를 사용하지 않으면 새로 정보가 갱신되지 않음(필수 메서드)
        recipe.refresh_from_db()
        # recipe.title 이 'sample recipe' 에서 Chicken Stew' 로 갱신 되었는지 확인
        self.assertEqual(recipe.title, payload['title'])
        # Many-To-Many 필드에서 tag 속성의 len()은 objects Manager 을 사용할 수 없기 때문에
        #   tags 변수에 해당 recipe 의 모든 tag 를 쿼리셋으로 가져옴
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        """
        put 을 통한 recipe 업데이트 테스트

        put: 자원의 전체를 수정(요청 시에 해당하는 자원 모두를 필요로 함)
        """
        # 계속 사용하게 되는 이 self.user 는 force_authenticate() 로 인증된 유저임을 기억해둘 것
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))

        payload = {
            'title': 'Tomato Spaghetti',
            'time_minutes': 25,
            'price': 5.00
        }
        url = detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)


class RecipeImageUploadTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@master.com',
            'pass1234'
        )
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        """recipe 에 이미지를 업로딩하는 테스트"""
        url = image_upload_url(self.recipe.id)
        # tempfile 은 특정 scope 안에서 사용되다가 사라짐
        # NamedTemporaryFile 은 파일 이름을 반드시 가져야 함
        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp:
            # PIL.Image 는 이미지를 로드 또는 생성하는 기능을 가지고 있음
            # 10 x 10 이미지 파일 생성
            img = Image.new('RGB', (10, 10))
            img.save(temp, format('JPEG'))
            temp.seek(0)
            res = self.client.post(url, {'image': temp}, format('multipart'))

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """유효하지 않은 이미지를 업로딩 할 경우 테스트"""
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image': 'notimage'}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_recipes_by_tags(self):
        """tag 가 있는 recipe 만 리턴되는지 테스트"""
        recipe1 = sample_recipe(user=self.user, title='Poo Phat Pong Curry')
        recipe2 = sample_recipe(user=self.user, title='Kimchi soup')
        tag1 = sample_tag(user=self.user, name='Yummy')
        tag2 = sample_tag(user=self.user, name='good place')
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)
        recipe3 = sample_recipe(user=self.user, title='Fish and chips')

        res = self.client.get(RECIPES_URL, {'tags': f'{tag1.id}, {tag2.id}'})

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_recipes_by_ingredients(self):
        """ingredients 가 있는 recipe 만 리턴되는지 테스트"""
        recipe1 = sample_recipe(user=self.user, title='Combination Pizza')
        recipe2 = sample_recipe(user=self.user, title='Tomato spaghetti')
        ingredient1 = sample_ingredient(user=self.user, name='milk')
        ingredient2 = sample_ingredient(user=self.user, name='tomato')
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)
        recipe3 = sample_recipe(user=self.user, title='Cheese cake')

        res = self.client.get(RECIPES_URL, {'ingredients': {f'{ingredient1.id},{ingredient2.id}'}})

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)
