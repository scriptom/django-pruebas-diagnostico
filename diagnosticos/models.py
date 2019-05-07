from django.db import models
from django.conf import settings
from django.utils.functional import cached_property
from django.utils.timezone import now
from datetime import timedelta
from django.utils.translation import ugettext as _
from django.utils.text import slugify

# Create your models here.


class PoolPreguntas(models.Model):
    """
    Modelo que facilita el acceso a un grupo de preguntas mediante un nombre comun
    """
    nombre = models.CharField(_("Nombre del banco"), max_length=30)
    slug = models.SlugField(_("Slug del banco"), editable=False)

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        self.slug = slugify(self.nombre)
        super(PoolPreguntas, self).save(*args, **kwargs)

    class Meta:
        db_table = 'pool_preguntas'
        verbose_name = 'Banco de Preguntas'
        verbose_name_plural = 'Bancos de Preguntas'


class Pregunta(models.Model):
    """
    Modelo que representa una pregunta
    """
    texto_pregunta = models.TextField(max_length=255)
    pool = models.ForeignKey(
        'PoolPreguntas',
        verbose_name='Banco de Preguntas',
        on_delete=models.CASCADE,
        null=True,
        related_name='preguntas'
    )

    def __str__(self):
        return self.texto_pregunta

    def excerpt(self, length=50):
        """
        Devuelve un extracto de longitud 'length' del texto 
        de esta pregunta
        """
        if len(self.texto_pregunta) > length:
            return self.texto_pregunta[0:length+1] + '...'
        return self.texto_pregunta


class PreguntasPrueba(models.Model):
    """
    Aparicion de una Pregunta en una prueba
    """
    prueba = models.ForeignKey(
        "Diagnostico",
        on_delete=models.CASCADE,
        editable=False,
        related_name='preguntas_usadas'
    )

    pregunta = models.ForeignKey(
        "Pregunta",
        on_delete=models.CASCADE,
        related_name='apariciones'
    )

    respuesta = models.ForeignKey(
        "Respuesta",
        on_delete=models.CASCADE,
        null=True,
        related_name='seleccion_usuarios'
    )

    @property
    def es_correcta(self):
        for respuesta in self.pregunta.respuestas.all():
            if respuesta.pk == self.respuesta.pk:
                return respuesta.es_correcta
        return False

    def __str__(self):
        return str(self.pregunta)


class Respuesta(models.Model):
    """
    Modelo que representa una respuesta, almacena informacion sobre la pregunta que responde, el texto de respuesta y la veracidad 
    de la misma
    """
    texto_respuesta = models.CharField(
        max_length=255)

    pregunta = models.ForeignKey(
        'Pregunta',
        on_delete=models.CASCADE,
        related_name='respuestas'
    )

    es_correcta = models.BooleanField(
        verbose_name='correcta?',
        default=False
    )

    def __str__(self):
        return self.texto_respuesta

    class Meta:
        db_table = 'respuestas'


class Diagnostico(models.Model):
    """
    Modelo que representa una prueba diagnostico.
    Una prueba diagnostico se entiende como la seleccion aleatoria de preguntas relacionadas por un pool comun, y esta asociada a un usuario
    """
    banco = models.ForeignKey(
        "PoolPreguntas",
        verbose_name="Banco de preguntas",
        on_delete=models.PROTECT,
        related_name='pruebas_del_banco'
    )

    resultado = models.PositiveSmallIntegerField(
        null=True,
        editable=False
    )

    fecha_presentacion = models.DateTimeField(
        'Fecha de presentación de la prueba',
        auto_now=True,
        editable=False
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Usuario",
        on_delete=models.CASCADE,
        related_name="pruebas_presentadas"
    )

    preguntas = models.ManyToManyField(
        "Pregunta",
        verbose_name="Preguntas de la prueba",
        through='PreguntasPrueba'
    )

    def __str__(self):
        nota = self.resultado or "Sin presentar"
        return '{usuario} en {fecha}: {resultado}'.format(usuario=self.usuario, fecha=self.fecha_presentacion, resultado=nota)

    @property
    def resumen(self):
        string = ''
        for pregunta_indice in range(len(self.preguntas.all())):
            num_pregunta = pregunta_indice + 1 
            texto_pregunta = self.preguntas.all()[pregunta_indice]
            opcion_usuario = self.preguntas_usadas.all()[pregunta_indice].respuesta
            correcta = self.preguntas.all()[pregunta_indice].respuestas.get(es_correcta=True)
            format_dict = {
                'num_pregunta': num_pregunta,
                'texto_pregunta': texto_pregunta,
                'opcion_usuario': opcion_usuario,
                'correcta': correcta
            }
            string += '{num_pregunta}. {texto_pregunta}\n - Resp: {opcion_usuario} (Correcta: {correcta})\n'.format(**format_dict)
        string += 'Nota total: %i' % self.resultado
        return string

    @property
    def is_valid(self):
        """
        Determina si la prueba en cuestion es valida (vigente)
        Nota: En desarrollo siempre tiene que devolver True
        """
        if settings.DEBUG:
            return True
        if self.fecha_presentacion:
            return (now() - self.fecha_presentacion) >= timedelta(days=365)
        return True

    def evaluar(self):
        """
        Metodo que corrige la prueba diagnostico.
        """
        # si ya tenemos una nota, simplemente vamos a devolverla
        if self.resultado is None:
            # Iniciamos la cuenta de respuestas correctas
            nota = 0
            # Iteramos sobre las preguntas usadas en esta prueba
            for respuesta_usuario in self.preguntas_usadas.all():
                # Nos preguntamos si la pregunta es correcta. De serlo, entonces aumentamos en 1 la puntuacion
                if respuesta_usuario.es_correcta:
                    nota += 1
            # Salvamos la nota en el resultado de la instancia
            self.resultado = nota

        return self.resultado

    def save(self, *args, **kwargs):
        """
        Prevencion de guardado de pruebas invalidas, e implementacion de evaluacion en guardado
        """
        if self.is_valid:
            if self.resultado is None:
                self.evaluar
            super(Diagnostico, self).save(*args, **kwargs)
