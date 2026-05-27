from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType



class UIDObjectMixin:
    model = None

    def get_object(self):
        uid = self.kwargs.get('uid')
        return get_object_or_404(self.model, uid=uid)


class GenericAttachMixin:
    """Resolves any model instance from content_type + uid."""
    def get_target_object(self):
        content_type_id = self.kwargs.get("content_type_id")
        obj_uid         = self.kwargs.get("obj_uid")
        content_type    = get_object_or_404(ContentType, id=content_type_id)
        model_class     = content_type.model_class()
        return get_object_or_404(model_class, uid=obj_uid)


class UserTrackingMixin:
    """Automatically sets created_by to the logged-in user on create."""
    def form_valid(self, form):
        if self.request.user and self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
        return super().form_valid(form)