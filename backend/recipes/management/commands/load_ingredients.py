import csv
import logging
from django.core.management.base import BaseCommand
from recipes.models import Ingredient

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Загрузить данные об ингредиентах из CSV-файла в БД.'

    def handle(self, *args, **kwargs):
        try:
            with open(
                'recipes/data/ingredients.csv',
                'r',
                encoding='UTF-8'
            ) as ingredients:
                reader = csv.reader(ingredients)
                for row in reader:
                    if len(row) == 2:
                        name, measurement_unit = row
                        ingredient, created = Ingredient.objects.get_or_create(
                            name=name.strip(),
                            measurement_unit=measurement_unit.strip(),
                        )
                        if created:
                            logger.info(f'Создан ингредиент: {ingredient}')
                        else:
                            logger.info(
                                f'Ингредиент уже существует: {ingredient}'
                            )
                    else:
                        logger.warning(f'Неверная строка пропущена: {row}')
        except FileNotFoundError:
            logger.error('Указанный CSV файл не найден.')
        except Exception as e:
            logger.error(f'Произошла ошибка: {e}')
