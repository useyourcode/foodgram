from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    first_name = models.CharField('Имя', max_length=150, blank=False)
    last_name = models.CharField('Фамилия', max_length=150, blank=False)
    username = models.CharField(
        'Имя пользователя',
        max_length=150,
        unique=True,
    )

    email = models.EmailField(
        'Почта',
        unique=True,
        max_length=150,
        blank=False
    )

    avatar = models.ImageField(
        blank=True,
        null=True,
        upload_to='media/avatars'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return self.username


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "subscriber",
                    "author",
                ),
                name="unique_follow",
            )
        ]

    def clean(self):
        if self.subscriber == self.author:
            raise ValidationError("Нельзя подписаться на самого себя.")
        super().clean()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.subscriber.username} подписан на {self.author.username}'
