import djoser.serializers
from django.shortcuts import get_object_or_404
from django.urls import reverse
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (
    Favorite,
    Ingredient,
    IngredientToRecipe,
    Recipe,
    ShopList,
    Tag
)
from users.models import User
from linklite.models import URL

MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 2880


class UserSerializer(djoser.serializers.UserSerializer):
    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'id', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')
        validators = [
            UniqueTogetherValidator(
                queryset=User.objects.all(),
                fields=('username', 'email')
            )
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return obj.subscriptions.filter(id=request.user.id).exists()


class AvatarSerializer(serializers.ModelSerializer):

    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)


class UserCreateSerializer(djoser.serializers.UserCreateSerializer):

    class Meta:
        model = User
        fields = (
            'email', 'username', 'first_name',
            'last_name', 'password', 'avatar')

    class UserUpdateSerializer(serializers.ModelSerializer):
        avatar = Base64ImageField(max_length=None, use_url=True)

        class Meta:
            model = User
            fields = (
                'email', 'username', 'first_name',
                'last_name', 'avatar')


class SubscribeListSerializer(djoser.serializers.UserSerializer):
    recipes_count = SerializerMethodField()
    recipes = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'recipes',
            'recipes_count',
        )
        read_only_fields = ('email', 'username',
                            'first_name', 'last_name')

    def validate(self, data):
        request = self.context.get('request')
        author_id = request.parser_context.get('kwargs').get('id')
        author = get_object_or_404(User, id=author_id)
        user = request.user
        if user.subscriptions.filter(author=author_id).exists():
            raise ValidationError(
                'Вы уже подписаны',
                code=status.HTTP_400_BAD_REQUEST
            )
        if user == author:
            raise ValidationError(
                'Ты не можешь подписаться на себя',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = int(request.GET.get('recipes_limit', 0))
        recipes = obj.recipes.all()[:limit] if limit else obj.recipes.all()
        serializer = RecipeShortSerializer(recipes, many=True, read_only=True)
        return serializer.data


class RecipeShortSerializer(serializers.ModelSerializer):

    class Meta:
        fields = (
            'name', 'text', 'cooking_time',
            'image',
        )
        model = Recipe


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'name', 'color', 'slug')
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredient


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source='ingredient.id'
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientToRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class IngredientRecipeForCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = IngredientToRecipe
        fields = ('id', 'amount',)


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=False, many=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientRecipeSerializer(
        many=True,
        source='ingredient_to_recipe')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(max_length=None)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time'
                  )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (request.user.is_authenticated
                and obj.favorites.filter(user=request.user).exists())

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (request.user.is_authenticated
                and obj.shopping_list.filter(user=request.user).exists())


class CreateRecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientRecipeForCreateSerializer(
        many=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        error_messages={'does_not_exist': 'Тега не существует'}
    )
    image = Base64ImageField(max_length=None)
    author = UserSerializer(read_only=True)
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time')

    def validate(self, data):
        recipe_id = self.instance.id if self.instance else None
        if Recipe.objects.filter(
            text=data["text"]
        ).exclude(id=recipe_id).exists():
            raise serializers.ValidationError(
                'Этот рецепт уже есть.'
            )
        return data

    def validate_tags(self, tags):
        if len(set(tags)) != len(tags):
            raise serializers.ValidationError('Теги должны быть уникальны.')
        if not tags:
            raise serializers.ValidationError('Отсутствуют теги')
        return tags

    def validate_cooking_time(self, cooking_time):
        if cooking_time < MIN_COOKING_TIME:
            raise serializers.ValidationError(
                'Минимум 1 минута')
        if cooking_time > MAX_COOKING_TIME:
            raise serializers.ValidationError(
                'Время готовки должно быть не больше 2 суток')
        return cooking_time

    def validate_ingredients(self, ingredients):
        ingredients_list = []

        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            if ingredient_id in ingredients_list:
                raise serializers.ValidationError(
                    'Добавили одинаковые ингредиенты.'
                )
            ingredients_list.append(ingredient_id)

            if int(ingredient.get('amount', 0)) < 1:
                raise serializers.ValidationError('Не добавили ингредиенты')
        return ingredients

    @staticmethod
    def add_tags_and_ingredients_to_recipe(recipe, tags, ingredients):
        recipe.tags.set(tags)
        IngredientToRecipe.objects.bulk_create([
            IngredientToRecipe(
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount'],
                recipe=recipe
            ) for ingredient_data in ingredients
        ])

    def create(self, validated_data):
        request = self.context.get('request', None)
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=request.user, **validated_data)
        self.add_tags_and_ingredients_to_recipe(recipe, tags, ingredients)
        return recipe

    def update(self, recipe, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        if tags is not None:
            recipe.tags.set(tags)
        if ingredients is not None:
            IngredientToRecipe.objects.filter(recipe=recipe).delete()
            self.add_tags_and_ingredients_to_recipe(recipe, tags, ingredients)
        return super().update(recipe, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context={
            'request': self.context.get('request')
        }).data


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        fields = (
            'recipe', 'user'
        )
        model = Favorite

    def validate(self, data):
        user = data['user']
        if user.favorites.filter(recipe=data['recipe']).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в избранное.'
            )
        return data

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class ShopListSerializer(serializers.ModelSerializer):

    class Meta:
        fields = (
            'recipe', 'user'
        )
        model = ShopList

    def validate(self, data):
        user = data['user']
        if user.shopping_list.filter(recipe=data['recipe']).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен'
            )
        return data

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class LinkLiteSerializer(serializers.ModelSerializer):

    class Meta:
        model = URL
        fields = ('original_url',)
        write_only_fields = ('original_url',)

    def get_short_link(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(
            reverse('linklite:take_url', args=[obj.url_hash])
        )

    def create(self, validated_data):
        instance, _ = URL.objects.get_or_create(**validated_data)
        return instance

    def to_representation(self, instance):
        return {'short-link': self.get_short_link(instance)}
