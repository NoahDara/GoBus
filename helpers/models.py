from django.db import models
import uuid
from django.contrib.contenttypes.models import ContentType
from simple_history.utils import update_change_reason
from simple_history.models import HistoricalRecords

class BaseModel(models.Model):
    """
    Abstract base model that all models should inherit from.
    Provides common fields: is_active, is_deleted, created, updated
    Automatically orders by most recently updated first
    """
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True, editable=False)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    
    class Meta:
        abstract = True
        ordering = ['-updated', '-created']
        
        
    @property
    def content_type(self):
        """
        Get ContentType for this model instance.
        Returns the ContentType object for this model.
        """
        return ContentType.objects.get_for_model(self.__class__)