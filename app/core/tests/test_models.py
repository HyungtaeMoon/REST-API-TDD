from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model

from ..models import Tag, Ingredient, Recipe, recipe_image_file_path


def sample_user(email='hello@world.com', password='test123123'):
    """sample user 생성"""
    return get_user_model().objects.create_user(email, password)


class ModelTest(TestCase):

    def test_create_user_with_email_successful(self):
        """이메일을 포함하여 유저가 계정을 생성했을 때 테스트 코드"""
        email = 'hello@world.com'
        password = 'test123123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalize(self):
        """새로운 유저의 이메일 필드를 표준화(도메인을 소문자로 저장)"""
        email = 'hello@WORLD.COM'
        user = get_user_model().objects.create_user(email, 'password123')

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """유저의 이메일 형식이 올바르지 않을 경우"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'password123')

    def test_new_create_superuser(self):
        user = get_user_model().objects.create_superuser(
            'master1@world.com',
            'password123'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        """tag 문자열이 일치하는지 테스트"""
        tag = Tag.objects.create(
            user=sample_user(),
            name='Steve'
        )

        self.assertEqual(str(tag), tag.name)

    def test_ingredient_str(self):
        """레시피 성분의 문자열 테스트"""
        ingredient = Ingredient.objects.create(
            user=sample_user(),
            name='Cucumber'
        )

        self.assertEqual(str(ingredient), ingredient.name)

    def test_recipe_str(self):
        """레시피의 문자열 테스트"""
        recipe = Recipe.objects.create(
            user=sample_user(),
            title='Steak and mushroom sauce',
            time_minutes=5,
            price=5.00
        )

        self.assertTrue(str(recipe), recipe.title)

    # models.recipe_image_file_path 에서 uuid4() 메서드 사용
    @patch('uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        """올바른 위치에 이미지 파일이 저장되는지 테스트"""
        uuid = 'test-uuid'
        # uuid.uuid4 를 오버라이딩하여 uuid 는 'test-uuid' 로 사용됨
        mock_uuid.return_value = uuid
        # recipe_image_file_path 에서 instance 는 받지 않기 때문에 None
        file_path = recipe_image_file_path(None, 'myimage.jpg')

        # uploads/recipe/test-uuid.jpg
        exp_path = f'uploads/recipe/{uuid}.jpg'
        self.assertEqual(file_path, exp_path)
