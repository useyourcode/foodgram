from django.contrib import admin

from .models import Subscription, User


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username', 'first_name', 'last_name', 'email',
    )
    search_fields = ('username',)
    list_filter = ('username', 'email')
    ordering = ('username',)
    empty_value_display = '-'


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'subscriber', 'author'
    )
    search_fields = ('subscriber',)
    list_filter = ('subscriber', 'author')
    ordering = ('subscriber',)
    empty_value_display = '-'


admin.site.register(User, UserAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
