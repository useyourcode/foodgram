from colorfield.fields import ColorField
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models

from users.models import User


class Tag(models.Model):
    name = models.CharField('Название', max_length=200, unique=True)
    slug = models.SlugField('Slug', unique=True)
    color = ColorField(
        'Цвет', max_length=7, default="#ffffff", unique=True, format='hex',
        validators=[
            RegexValidator(
                regex="^#([a-f0-9]{6}|[a-f0-9]{3})$",
                message='Некорректный формат',
            )
        ],
    )
    class Meta:
        ordering = ('name',)
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=100, db_index=True)
    measurement_unit = models.CharField('Еденица измерения', max_length=30)

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_measurement_unit'
            )
        ]

    def __str__(self):
        return f'{self.name[:10]} {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='автор',
        related_name='recipes'
    )
    name = models.CharField('Название', max_length=200)
    text = models.TextField('Описание')
    image = models.ImageField('Изображение', upload_to='recipes/image/')
    description = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления в минутах',
        validators=[
            MinValueValidator(
                1, message='Поставь хотя бы минуту'),
            MaxValueValidator(1000)
        ]
    )

    tags = models.ManyToManyField(
        Tag, through='TagToRecipe',
        verbose_name=('Теги'),
        related_name='recipes'
    )

    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientToRecipe',
        verbose_name='Ингридиенты',
        related_name='recipes'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = ('Рецепт')
        verbose_name_plural = ('Рецепты')
        constraints = [
            models.UniqueConstraint(
                fields=['text', 'author'],
                name='unique_text_author'
            )
        ]

    def __str__(self):
        return self.name[:10]


class TagToRecipe(models.Model):
    tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE, verbose_name='тег',
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='рецепт',
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return f'{self.tag} + {self.recipe}'


class IngredientToRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name='ингридиент',
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='рецепт',
        related_name='ingredienttorecipe'
    )

    amount = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(1000)],
        verbose_name='Количество ингредиента',
        default=1
    )

    class Meta:
        verbose_name = 'ингридиент'
        verbose_name_plural = 'ингридиенты'

    def __str__(self):
        return f'{self.ingredient} + {self.recipe}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',

    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.user} :: {self.recipe}'


class Favorite(ShoppingCart):

    class Meta:
        default_related_name = 'favorites'
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

        def __str__(self):
            return (f' рецепт {Favorite.recipe}'
                    f'в избранном пользователя {Favorite.user}')


class ShopList(ShoppingCart):

    class Meta:
        default_related_name = 'shopping_list'
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'

    def __str__(self):
        return (f' рецепт {ShopList.recipe}'
                f'в корзине пользователя {ShopList.user}')
