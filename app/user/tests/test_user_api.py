from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')


def create_user(**params):
    """새로운 사용자 생성을 위한 Helper function"""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """user API 테스트(public)"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """유효한 payload 의 사용한 유저 생성"""
        payload = {
            'email': 'customer@test.com',
            'password': 'pass1234',
            'name': 'smith',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))
        # 보안상의 이유로 request 에는 비밀번호가 담기지 않아야 한다.
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        """이미 유저가 존재할 경우에는 400 코드를 반환하는지에 대한 테스트"""
        payload = {'email': 'admin@test.com', 'password': 'pass1234'}
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """비밀번호가 5 글자가 되지 않을 때 실패를 반환하는지 테스트"""
        payload = {'email': 'admin@test.com', 'password': 'pass'}
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """유저를 생성할 때 토큰이 생성되는지 테스트"""
        payload = {'email': 'customer@test.com', 'password': 'password123'}
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """비밀번호가 틀렸을 경우 토큰이 생성되지 않아야 한다는 테스트"""
        create_user(email='customer@test.com', password='pass1234')
        payload = {'email': 'customer@test.com', 'password': 'wrong'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """유저가 없을 경우 토큰이 생성되지 않아야 한다는 테스트"""
        payload = {'email': 'customer@test.com', 'password': 'pass1234'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """필드에 항목을 채우지 않고 요청을 보낼 경우에 대한 테스트"""
        res = self.client.post(TOKEN_URL, {'email': 'one', 'password': ''})
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
