from django_filters import rest_framework as filters
from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(filters.FilterSet):

    name_startswith = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    name_contains = filters.CharFilter(
        field_name='name',
        lookup_expr='icontains'
    )

    class Meta:
        model = Ingredient
        fields = []

    def filter_queryset(self, queryset):
        if 'name_startswith' in self.data:
            queryset = queryset.filter(
                name__istartswith=self.data['name_startswith']
            )

        if 'name_contains' in self.data:
            queryset = queryset.filter(
                name__icontains=self.data['name_contains']
            )

        return queryset


class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(method='filter_by_user_favorites')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_by_user_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']

    def filter_by_user_favorites(self, queryset, name, value):
        return self.filter_by_user_relationship(queryset, value, 'favorites')

    def filter_by_user_shopping_cart(self, queryset, name, value):
        return self.filter_by_user_relationship(
            queryset,
            value,
            'shopping_list'
        )

    def filter_by_user_relationship(self, queryset, value, relationship):
        if value and self.request.user.is_authenticated:
            filter_key = f'{relationship}__user'
            return queryset.filter(**{filter_key: self.request.user})
        return queryset
