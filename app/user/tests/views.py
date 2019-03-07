from rest_framework import generics
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from .serializers import UserSerializer, AuthTokenSerializer


class CreateUserView(generics.CreateAPIView):
    """시리얼라이저 유저 생성"""
    serializer_class = UserSerializer


class CreateTokenView(ObtainAuthToken):
    """유저에 대한 새로운 인증 토큰 생성"""
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
