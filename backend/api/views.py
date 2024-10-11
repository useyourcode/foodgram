from io import BytesIO

from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from recipes.make_pdf import make_pdf_file
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    ShopList,
    Tag
)
from users.models import Subscription, User
from .filter import RecipeFilter
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
    UserSerializer
)


class UserViewSet(UserViewSet):
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
        user = request.user
        author = get_object_or_404(User, pk=id)

        if request.method == 'POST':
            serializer = SubscribeListSerializer(
                author, data=request.data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(subscriber=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        get_object_or_404(
            Subscription, subscriber=user, author=author
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

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
    filter_backends = (DjangoFilterBackend,)
    pagination_class = None
    search_fields = ('name', )


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
        if self.request.method == 'GET':
            return RecipeReadSerializer
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
        return self.add_to_list(request, pk)

    @shopping_cart.mapping.delete
    def destroy_shopping_cart(self, request, pk):
        self.model = ShopList
        return self.remove_from_list(request, pk)

    @action(
        detail=True,
        methods=('POST',),
        permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        self.serializer_class = FavoriteSerializer
        self.model = Recipe
        return self.add_to_list(request, pk)

    @favorite.mapping.delete
    def destroy_favorite(self, request, pk):
        self.model = Favorite
        return self.remove_from_list(request, pk)
