from io import BytesIO

from django.http import FileResponse, HttpResponse
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.urls import reverse

from recipes.make_pdf import make_pdf_file
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    ShopList,
    Tag
)
from users.models import Subscription, User
from .filter import RecipeFilter, IngredientFilter
from .mixin import AddRemoveMixin
from .pagination import CustomPagination
from .permissions import AuthorPermission
from .serializers import (
    AvatarSerializer,
    CreateRecipeSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    ShopListSerializer,
    SubscribeListSerializer,
    TagSerializer,
    UserSerializer,
    LinkLiteSerializer,
)


class UserViewSet(UserViewSet, AddRemoveMixin):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination

    @action(
        methods=('get',),
        detail=False,
        permission_classes=(IsAuthenticatedOrReadOnly,)
    )
    def get_self_page(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticatedOrReadOnly,)
    )
    def subscribe(self, request, id):
        self.serializer_class = SubscribeListSerializer
        self.model = User
        self.related_model = Subscription
        self.model_field = 'author'

        if request.method == 'POST':
            return self.add_to_list(request, id)
        return self.remove_from_list(request, id)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(subscribers__subscriber=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeListSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['put'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
        url_name='me-avatar',
    )
    def avatar(self, request):
        serializer = self._change_avatar(request.user, request.data)
        return Response(serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        data = {'avatar': None}
        self._change_avatar(request.user, data)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _change_avatar(self, user, data):
        serializer = AvatarSerializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = IngredientFilter
    pagination_class = None


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet, AddRemoveMixin):
    queryset = Recipe.objects.all()
    serializer_class = CreateRecipeSerializer
    permission_classes = (AuthorPermission,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeReadSerializer
        elif self.action == 'get_link':
            return LinkLiteSerializer
        elif self.action == 'favorite':
            return FavoriteSerializer
        elif self.action == 'shopping_cart':
            return ShopListSerializer
        return CreateRecipeSerializer

    @staticmethod
    def generate_shopping_list(ingredients):
        items = [
            "{name} ({unit}) - {amount}".format(
                name=ing['ingredient__name'],
                unit=ing['ingredient__measurement_unit'],
                amount=ing['total_amount']
            ) for ing in ingredients
        ]
        shopping_list = "Купить в магазине:\n" + "\n".join(items)
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(detail=False, methods=['GET'])
    def download_shopping_cart(self, request):
        ingredients = ShopList.get_shopping_ingredients(request.user)
        pdf_file = make_pdf_file(ingredients, [], request)
        return FileResponse(
            BytesIO(pdf_file),
            as_attachment=True,
            filename='shopping_list.pdf'
        )

    @action(
        detail=True,
        methods=('POST',),
        permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        self.serializer_class = ShopListSerializer
        self.model = Recipe
        self.related_model = ShopList
        self.model_field = 'recipe'
        if request.method == 'POST':
            return self.add_to_list(request, pk)
        return self.remove_from_list(request, pk)

    @shopping_cart.mapping.delete
    def destroy_shopping_cart(self, request, pk):
        self.model = Recipe
        self.related_model = ShopList
        self.model_field = 'recipe'
        return self.remove_from_list(request, pk)

    @action(
        detail=True,
        methods=('POST',),
        permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        self.serializer_class = FavoriteSerializer
        self.model = Recipe
        self.related_model = Favorite
        self.model_field = 'recipe'
        if request.method == 'POST':
            return self.add_to_list(request, pk)
        return self.remove_from_list(request, pk)

    @favorite.mapping.delete
    def destroy_favorite(self, request, pk):
        self.model = Recipe
        self.related_model = Favorite
        self.model_field = 'recipe'
        return self.remove_from_list(request, pk)

    @action(
        methods=['get'],
        detail=True,
        url_path='get-link',
        url_name='get-link',
    )
    def get_link(self, request, pk=None):
        self.get_object()

        original_url = request.META.get('HTTP_REFERER')
        if original_url is None:
            url = reverse('api:recipe-detail', kwargs={'pk': pk})
            original_url = request.build_absolute_uri(url)

        serializer = self.get_serializer(
            data={'original_url': original_url},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)
