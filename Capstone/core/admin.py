from django.contrib import admin
from .models import Persona, Auto, Profile, RegistroEntradaSalida

# Register your models here.
admin.site.register(Persona)
admin.site.register(Auto)
admin.site.register(Profile)
admin.site.register(RegistroEntradaSalida)