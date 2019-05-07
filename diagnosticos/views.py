import datetime

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView

from .forms import PreguntasPruebaForm, PreguntasPruebaFormSet
from .models import Diagnostico, PoolPreguntas, Pregunta, PreguntasPrueba


@method_decorator(login_required, name='dispatch')
class PresentarView(FormView):
    """
    Vista de presentacion de una prueba. Contiene un formset de preguntas.
    Esta protegida para que solo los que hayan iniciado sesion puedan verla
    """
    template_name = 'diagnostico_presentar.html'
    form_class = PreguntasPruebaFormSet
    initial = []
    success_url = 'diagnosticos:prueba-detalle'

    def get(self, request, *args, **kwargs):
        """
        Metodo para mostrar el formulario de presentacion de una prueba.
        """
        self.diagnostico = self.get_quiz_instance()

        # obtenemos un queryset de preguntas aleatorias del pool dado, limitado a 20
        self.preguntas_qs = Pregunta.objects.filter(
            pool=self.diagnostico.banco).order_by('?').distinct()[:20]
        self.preguntas = self.get_question_list(self.diagnostico)
        for pregunta in self.preguntas_qs:
            # iteramos sobre ellas y las agregamos a la prueba que estamos llenando
            self.preguntas.append(PreguntasPrueba.objects.create(
                prueba=self.diagnostico, pregunta=pregunta))
        self.diagnostico.refresh_from_db()

        return super(PresentarView, self).get(request, *args, **kwargs)

    def get_question_list(self, quiz):
        """
        Retorna una lista con las preguntas usadas en esta prueba
        """
        preguntas = []
        if quiz.preguntas_usadas is None:
            queryset = Pregunta.objects.filter(
                pool=self.diagnostico.banco).order_by('?').distinct()[:20]
            for pregunta in queryset:
                preguntas.append(PreguntasPrueba.objects.create(
                    prueba=self.diagnostico, pregunta=pregunta))
            self.diagnostico.refresh_form_db()
        else:
            preguntas = [
                pregunta for pregunta in quiz.preguntas_usadas.all()]
        return preguntas

    def get_quiz_instance(self):
        """
        Metodo para obtener la instancia de prueba diagnostico relacionada
        """
        if self.request.method == 'POST':
            diagnostico = get_object_or_404(
                Diagnostico, pk=self.request.POST['quiz_id'])
        elif self.request.method == 'GET':
            banco = self.get_question_pool()
            diagnostico = Diagnostico.objects.create(
                usuario=self.request.user, banco=banco)
        return diagnostico

    def get_question_pool(self):
        """
        Metodo para obtener de la peticion el objeto del pool correspondiente
        """
        pk = self.request.GET.get('banco', None)
        return get_object_or_404(PoolPreguntas, pk=pk)

    def form_valid(self, form):
        """
        En caso de que el formulario sea valido, lo guardamos
        """
        self.instance = form.save()[0].prueba
        self.instance.evaluar()
        self.instance.save()
        return super(PresentarView, self).form_valid(form)

    def get_initial(self):
        """
        Metodo para tener el formset inicial de la prueba
        """
        initial = super(PresentarView, self).get_initial()
        self.preguntas = self.get_question_list(self.diagnostico)
        initial.extend([{'pregunta': pregunta} for pregunta in self.preguntas])
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formset'] = context.pop('form')
        context['quiz_id'] = self.diagnostico.pk
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['queryset'] = self.diagnostico.preguntas_usadas.all()
        return kwargs

    def get_success_url(self):
        return reverse(self.success_url, kwargs={'pk': self.instance.pk})

    def post(self, request, *args, **kwargs):
        self.diagnostico = self.get_quiz_instance()
        return super(PresentarView, self).post(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class DiagnosticoDetailView(DetailView):
    model = Diagnostico
    template_name = "diagnostico_detail.html"
    queryset = Diagnostico.objects.all()
    context_object_name = 'prueba'

    def get_object(self, queryset=None):
        object = super().get_object(queryset=self.queryset)
        if object.usuario != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied(
                _('Usted no tiene permiso para ver esta prueba'))
        return object
