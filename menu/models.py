from django.db import models
from django.utils.translation import gettext_lazy as _

class Category(models.Model):
    """Food and Drink categories"""
    CATEGORY_TYPES = [
        ('food', 'Food'),
        ('drink', 'Drink'),
    ]
    
    name = models.CharField(_('category name'), max_length=100)
    category_type = models.CharField(_('type'), max_length=10, choices=CATEGORY_TYPES)
    description = models.TextField(_('description'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['category_type', 'name']
    
    def __str__(self):
        return f"{self.get_category_type_display()} - {self.name}"

class MenuItem(models.Model):
    """Food and Drink items"""
    name = models.CharField(_('item name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    price = models.DecimalField(_('price'), max_digits=8, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    image = models.ImageField(_('image'), upload_to='menu_items/', blank=True, null=True)
    is_available = models.BooleanField(_('is available'), default=True)
    preparation_time = models.IntegerField(_('preparation time (minutes)'), default=15)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('menu item')
        verbose_name_plural = _('menu items')
        ordering = ['category', 'name']
    
    def __str__(self):
        return self.name