import csv
import logging
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from recipes.models import Ingredient

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Загрузить данные об ингредиентах из CSV-файла в БД.'

    def handle(self, *args, **kwargs):
        csv_file_path = os.path.join(
            settings.BASE_DIR,
            'recipes/data/ingredients.csv'
        )

        if not os.path.exists(csv_file_path):
            logger.error(
                f'CSV файл не найден по пути: {csv_file_path}'
            )
            return

        ingredients_to_create = []

        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == 2:
                    name = row[0].strip()
                    measurement_unit = row[1].strip()
                    ingredients_to_create.append(
                        Ingredient(
                            name=name,
                            measurement_unit=measurement_unit
                        )
                    )
                else:
                    logger.warning(
                        f'Неверная строка пропущена: {row}'
                    )

        try:
            Ingredient.objects.bulk_create(ingredients_to_create)
            logger.info('Ингредиенты успешно добавлены!')
        except IntegrityError:
            logger.error('Некоторые ингредиенты уже существуют!')
