from django.contrib import admin
import nested_admin
from django import forms
from .models import Pregunta, Respuesta, Diagnostico, PoolPreguntas
# Register your models here.

class RespuestaInline(nested_admin.NestedTabularInline):
    model = Respuesta
    extra = 0

class PreguntaInline(nested_admin.NestedStackedInline):
    model = Pregunta
    inlines = [
        RespuestaInline
    ]
    extra = 0


class PoolPreguntasAdmin(nested_admin.NestedModelAdmin):
    inlines = [
        PreguntaInline
    ]

admin.site.register(PoolPreguntas, PoolPreguntasAdmin)