from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

# view 와 url 을 관례적으로 연결하기 위한 라우터를 생성
router = DefaultRouter()
router.register('tags', views.TagViewSet)
router.register('ingredients', views.IngredientViewSet)
router.register('recipes', views.RecipeViewSet)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls))
]
