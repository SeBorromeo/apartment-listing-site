from django.contrib import admin
from .models import Listing
from .models import Message

# Register your models here.
admin.site.register(Listing)
admin.site.register(Message)