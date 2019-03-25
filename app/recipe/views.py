from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Tag, Ingredient
from .serializer import TagSerializer, IngredientSerializer


class BaseRecipeAttrViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):
    """TagViewSet, IngredientViewSet 의 중복 코드를 Base 코드로 두어 처리"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """최근 인증된 사용자에 대해서만 객체 반환"""
        return self.queryset.filter(user=self.request.user).order_by('-name')

    def perform_create(self, serializer):
        """새로운 객체를 생성"""
        serializer.save(user=self.request.user)


class TagViewSet(BaseRecipeAttrViewSet):
    """데이터베이스의 태그 관리 """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(BaseRecipeAttrViewSet):
    """데이터베이스의 성분 관리"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
