from rest_framework import serializers

from core.models import Tag, Ingredient


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name')
        read_only_Fields = ('id',)


class IngredientSerializer(serializers.ModelSerializer):
    """성분 객체의 직렬화"""
    class Meta:
        model = Ingredient
        fields = ('id', 'name')
        read_only_Fields = ('id',)
