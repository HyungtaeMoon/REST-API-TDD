from django.test import TestCase
from django.contrib.auth import get_user_model

from ..models import Tag


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
