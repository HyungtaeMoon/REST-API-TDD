from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Tag, Ingredient, Recipe
from .serializer import TagSerializer, IngredientSerializer, RecipeSerializer,\
                        RecipeDetailSerializer, RecipeImageSerializer


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


class RecipeViewSet(viewsets.ModelViewSet):
    """데이터베이스의 레시피 관리"""
    serializer_class = RecipeSerializer
    queryset = Recipe.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """최근 인증된 사용자에 대해서만 객체 반환"""
        return self.queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        """적절한 serializer 클래스 반환"""
        # ModelViewSet.RetrieveMixin.retrieve
        if self.action == 'retrieve':
            return RecipeDetailSerializer

        # 내장 메서드인 upload_image 를 사용하여 action 이 들어오면 RecipeImageSerializer 를 리턴
        elif self.action == 'upload_image':
            return RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """새로운 recipe 생성"""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """recipe 에 image 업로드"""
        recipe = self.get_object()
        serializer = self.get_serializer(
            recipe,
            data=request.data,
        )

        if serializer.is_valid():
            # serializer.data: {'id': 13,
            #  'image': 'http://testserver/media/uploads/recipe/aa5e2215-de47-4143-9e60-88f3c7426007.jpg'}
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
