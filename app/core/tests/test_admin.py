from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from django.urls import reverse


class AdminSiteTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email='admin@TEST.COM',
            password='password123'
        )

        self.client.force_login(self.admin_user)

        self.user = get_user_model().objects.create_user(
            email='customer@TEST.COM',
            password='password123',
            name='smith'
        )

    def test_users_listed(self):
        """생성한 유저가 admin 페이지에 존재하는지 테스트"""
        # admin/core/user
        url = reverse('admin:core_user_changelist')
        res = self.client.get(url)

        # smith
        self.assertContains(res, self.user.name)
        # customer@test.com // normalize_email 적용으로 도메인은 소문자로 변환
        self.assertContains(res, self.user.email)

    def test_user_change_page(self):
        """유저의 edit 페이지가 작동하는지 테스트"""
        # admin//core/user/4/change
        url = reverse('admin:core_user_change', args=[self.user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_create_user_page(self):
        """"유저를 생성 페이지에 접근했을 때 status 200 코드를 받아오는지 테스트"""
        # admin/core/user/add
        url = reverse('admin:core_user_add')
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
