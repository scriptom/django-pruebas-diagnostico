from django import forms

from .models import PreguntasPrueba, Respuesta
from django.utils.safestring import mark_safe


class PlainTextWidget(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        return mark_safe(value) if value is not None else '-'


class PreguntasPruebaBaseFormSet(forms.BaseModelFormSet):
    model = PreguntasPrueba

    unique_fields = set(('texto_pregunta', 'respuesta'))
    @classmethod
    def get_default_prefix(cls):
        return 'pregunta'


class PreguntasPruebaForm(forms.ModelForm):
    texto_pregunta = forms.CharField(widget=PlainTextWidget, label="Pregunta")

    class Meta:
        model = PreguntasPrueba
        fields = ('texto_pregunta', 'respuesta')

        widgets = {
            'respuesta': forms.RadioSelect
        }

    def __init__(self, *args, **kwargs):
        super(PreguntasPruebaForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance is not None:
            self.fields['respuesta'].queryset = instance.pregunta.respuestas.all()
        self.fields['respuesta'].empty_label = None
        self.fields['texto_pregunta'].initial = instance.pregunta.texto_pregunta
        self.fields['texto_pregunta'].disabled = True


PreguntasPruebaFormSet = forms.modelformset_factory(
    PreguntasPrueba, form=PreguntasPruebaForm, formset=PreguntasPruebaBaseFormSet, max_num=20, extra=0)
