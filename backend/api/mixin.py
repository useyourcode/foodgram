from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response


class AddRemoveMixin:
    serializer_class = None
    model = None
    related_model = None
    model_field = None

    def add_to_list(self, request, pk):
        context = {"request": request}
        instance = get_object_or_404(self.model, id=pk)
        data = {
            'subscriber': request.user.id,
            self.model_field: instance.id
        }
        serializer = self.serializer_class(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save(subscriber=request.user, author=instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_from_list(self, request, pk):
        instance = get_object_or_404(self.model, id=pk)
        obj = get_object_or_404(
            self.related_model,
            user=request.user,
            **{self.model_field: instance}
        )
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
