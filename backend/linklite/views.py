from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET
from models import URL


@require_GET
def take_url(request, url_hash):
    url_instance = get_object_or_404(URL, url_hash=url_hash)

    original_url = url_instance.original_url

    return redirect(original_url)
