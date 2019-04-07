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
        # recipe 에 사용되지 않는 tag, ingredient 를 assigned_only 변수에 할당
        assigned_only = bool(int(self.request.query_params.get('assigned_only', 0)))
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)

        # recipe1.tags: 강남맛집, recipe2.tags: 강남맛집
        # 2개 모두 tags 가 강남맛집을 가져도 1개로 unique 한 값으로 인식하여 쿼리셋을 리턴
        # filter() 의 결과값을 리턴 시켜줘야 하기 때문에 self 는 삭제
        return queryset.filter(user=self.request.user).order_by('-name').distinct()
        # return self.queryset.filter(user=self.request.user).order_by('-name')

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

    def _params_to_ints(self, qs):
        """list 로 된 str 타입의 ID 를 int 타입으로 형변환"""
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """인증 된 유저의 recipe 필터 검색"""
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        # queryset 은 Recipe 모델이고, 이미 objects 매니저를 가지고 있기 때문에
        # 접근할 때는 objects 를 사용하지 않고, queryset.filter() 의 기능을 수행할 수 있다
        queryset = self.queryset
        if tags:
            # 해당하는 queryset 을 순회하여 str 을 int 로 형변환
            tag_ids = self._params_to_ints(tags)
            # 메인 모델인 recipe 에서 tag_ids 와 일치하는 tags 를 모두 쿼리셋으로 담는다
            queryset = queryset.filter(tags__id__in=tag_ids)
        if ingredients:
            ingredient_id = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredient_id)
        # http://127.0.0.1:8000/api/recipe/recipes/?tags=2&ingredients=1
        return queryset.filter(user=self.request.user)
        # """최근 인증된 사용자에 대해서만 객체 반환"""
        # return self.queryset.filter(user=self.request.user)

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
