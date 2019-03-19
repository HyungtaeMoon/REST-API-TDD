from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from ..serializer import TagSerializer


TAGS_URL = reverse('recipe:tag-list')


class PublicTagsApiTests(TestCase):
    """공개적으로 사용 가능한 태그의 API 테스트"""
    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """태그 검색에 필요한 로그인 테스트"""
        res = self.client.get(TAGS_URL)

        # 인증되지 않은 객체는 401 status code 를 받아야 함
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """인증된 유저의 태그 API 테스트"""
    def setUp(self):
        """유저를 생성하고 force_authenticate 까지 진행"""
        self.user = get_user_model().objects.create_user(
            'test@admin.com',
            'pass1234'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """태그 검색 테스트"""
        Tag.objects.create(user=self.user, name='Beef')
        Tag.objects.create(user=self.user, name='Noodle')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        # 하나 이상의 인스턴스 또는 쿼리셋을 직렬화 시키기 위해 many=True 설정
        # many=True 를 설정하지 않으면 단일 인스턴스 객체만 전달이 됨
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """인증된 유저만 결과값을 반환할 수 있는지 태그인지 테스트"""
        # user2 로 Tag 객체를 만듦. 그러나 이 객체는 인증받지 않은 인스턴스이기 때문에
        # 실제로는 self.user 인스턴스만 전달된다.
        user2 = get_user_model().objects.create_user(
            'other@admin.com',
            'pass1234'
        )
        Tag.objects.create(user=user2, name='Fruity')
        tag = Tag.objects.create(user=self.user, name='Comfort Food')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tag_successful(self):
        """새로 생성한 태그 테스트"""
        # payload 는 사용에 있어서 전송되는 데이터인데, 보안쪽에서는 이 payload 의 패킷을 분석한다.
        # 그러나 웹 개발에서는 단순히 body 에서 확인하고자 하는 데이터로 이해를 하고 넘어가자.
        payload = {'name': 'Simple'}
        self.client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()
        self.assertTrue(exists)

    def test_create_tag_invalid(self):
        """invalid 한 payload 의 태그를 생성했을 경우의 테스트"""
        payload = {'name': ''}
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
