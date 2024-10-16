import string
from random import choice, randint

from django.db import models

MIN_HASH_GEN = 8
MAX_HASH_GEN = 10
MAX_HASH_LENGTH = 15
URL_MAX_LENGTH = 2048


def generate_hash() -> str:
    return ''.join(
        choice(string.ascii_letters + string.digits)
        for _ in range(randint(MIN_HASH_GEN, MAX_HASH_GEN))
    )


class URL(models.Model):
    url_hash = models.CharField(
        max_length=MAX_HASH_LENGTH, default=generate_hash, unique=True
    )
    original_url = models.URLField(max_length=URL_MAX_LENGTH)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    click_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Ссылка'
        verbose_name_plural = 'Ссылки'

    def __str__(self):
        return f'{self.original_url} -> {self.url_hash}'

    def save(self, *args, **kwargs):
        while not self.pk and URL.objects.filter(url_hash=self.url_hash).exists():
            self.url_hash = generate_hash()
        super().save(*args, **kwargs)
