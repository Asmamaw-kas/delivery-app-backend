from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()

class UserAddress(models.Model):
    """User's saved addresses with map coordinates"""
    ADDRESS_TYPES = [
        ('home', 'Home'),
        ('work', 'Work'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(_('address type'), max_length=10, choices=ADDRESS_TYPES, default='home')
    label = models.CharField(_('label'), max_length=100, blank=True)
    full_address = models.TextField(_('full address'))
    latitude = models.DecimalField(_('latitude'), max_digits=13, decimal_places=11)
    longitude = models.DecimalField(_('longitude'), max_digits=13, decimal_places=11)
    is_default = models.BooleanField(_('is default'), default=False)
    apartment = models.CharField(_('apartment/unit'), max_length=50, blank=True)
    building = models.CharField(_('building'), max_length=100, blank=True)
    floor = models.CharField(_('floor'), max_length=20, blank=True)
    notes = models.TextField(_('delivery notes'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('user address')
        verbose_name_plural = _('user addresses')
        ordering = ['-is_default', 'created_at']
        unique_together = ['user', 'label']
    
    def __str__(self):
        return f"{self.user.username}'s {self.get_address_type_display()} Address"
    
    def save(self, *args, **kwargs):
        # Ensure only one default address per user
        if self.is_default:
            UserAddress.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)