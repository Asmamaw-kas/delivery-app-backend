from django.contrib import admin
from django.utils.translation import gettext_lazy as _

admin.site.site_header = _('Cafe Delivery Administration')
admin.site.site_title = _('Cafe Delivery Admin')
admin.site.index_title = _('Welcome to Cafe Delivery Admin Panel')