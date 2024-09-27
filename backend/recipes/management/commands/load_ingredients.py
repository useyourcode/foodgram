import json

from django.core.management.base import BaseCommand
from django.db import transaction
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load ingredients data from a JSON file to the DB.'

    def handle(self, *args, **kwargs):
        try:
            with open(
                'recipes/data/ingredients.json',
                'r',
                encoding='UTF-8'
            ) as file:
                ingredient_data = json.load(file)
                with transaction.atomic():
                    for ingredient in ingredient_data:
                        Ingredient.objects.get_or_create(**ingredient)
            self.stdout.write(self.style.SUCCESS('Данные успешно загружены'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR('Ошибка при загрузке данных: {}'.format(e))
            )
