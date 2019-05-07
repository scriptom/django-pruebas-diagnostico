from django.test import TestCase, Client
from django.utils.text import slugify
from django.urls import reverse
from django.forms import modelformset_factory
from django.contrib.auth import get_user_model
from diagnosticos.models import Pregunta, Respuesta, PoolPreguntas, PreguntasPrueba, Diagnostico
from diagnosticos.forms import PreguntasPruebaForm, PreguntasPruebaFormSet
import sys

# Create your tests here.


class CreacionBancosTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        Montaje inicial de data para los bancos
        """
        data = {
            'Preguntas de Matematica': {
                'Cuanto es 9x9': {
                    '24': False,  # 1
                    '91': False,  # 2
                    '81': True,  # 3
                    '64': False  # 4
                },
                'Cual es la raiz cuadrada de 16': {
                    '4': True,  # 5
                    '3.14': False,  # 6
                    '2': False,  # 7
                    '6': False  # 8
                },
                'PI es un numero': {
                    'Trascendental': False,  # 9
                    'Irracional': False,  # 10
                    'Racional': False,  # 11
                    'Natural': False,  # 12
                    'Entero': False,  # 13
                    'Trascendental e Irracional': True  # 14
                }
            },
        }
        cls.bancos = []
        for (slug, data_banco) in data.items():
            pool = PoolPreguntas.objects.create(slug=slug)
            for (texto_pregunta, data_respuestas) in data_banco.items():
                pregunta = pool.preguntas.create(texto_pregunta=texto_pregunta)
                for (texto_respuesta, es_correcta) in data_respuestas.items():
                    respuesta = pregunta.respuestas.create(
                        texto_respuesta=texto_respuesta, es_correcta=es_correcta)
                pregunta.refresh_from_db()
            pool.refresh_from_db()
            cls.bancos.append(pool)

        cls.user = get_user_model().objects.create_user(
            first_name="Tomas",
            last_name="El Fakih",
            email="tomas@elfak.ih",
            username="tcelfakih",
            password='1234simple'
        )

        cls.diagnostico = Diagnostico.objects.create(
            usuario=cls.user,
            banco=cls.bancos[0]
        )

        for pregunta in cls.bancos[0].preguntas.all():
            planteada = PreguntasPrueba.objects.create(
                prueba=cls.diagnostico,
                pregunta=pregunta
            )
        cls.diagnostico.refresh_from_db()
        return super().setUpTestData()

    @classmethod
    def tearDownClass(cls):
        # Pregunta.objects.all().delete()
        return super().tearDownClass()

    def test_numero_preguntas(self):
        """
        Verificacion del numero de preguntas totales que hay en un pool
        """
        self.assertEquals(self.bancos[0].preguntas.count(), 3)

    def test_numero_respuestas(self):
        """
        Verificacion de que el numero de respuestas por pregunta este bien
        """
        self.assertEquals(self.bancos[0].preguntas.all()[
                          2].respuestas.all().count(), 6)
        self.assertEquals(self.bancos[0].preguntas.all()[
                          0].respuestas.all().count(), 4)

    def test_texto_preguntas(self):
        """
        Verificacion de que los textos de las preguntas esten bien
        """
        self.assertEquals(self.bancos[0].preguntas.all()[
                          0].texto_pregunta, 'Cuanto es 9x9')
        self.assertEquals(self.bancos[0].preguntas.all()[
                          1].texto_pregunta, 'Cual es la raiz cuadrada de 16')
        self.assertEquals(self.bancos[0].preguntas.all()[
                          2].texto_pregunta, 'PI es un numero')

    def test_texto_respuestas(self):
        """
        Comprobacion de que los textos de las respuestas esten bien
        """
        self.assertEquals(self.bancos[0].preguntas.all()[
                          1].respuestas.all()[0].texto_respuesta, '4')
        self.assertEquals(self.bancos[0].preguntas.all()[
                          1].respuestas.all()[1].texto_respuesta, '3.14')
        self.assertEquals(self.bancos[0].preguntas.all()[
                          1].respuestas.all()[2].texto_respuesta, '2')
        self.assertEquals(self.bancos[0].preguntas.all()[
                          1].respuestas.all()[3].texto_respuesta, '6')

    def test_veracidad_respuestas(self):
        """
        Verificacion de veracidad de una respuesta (De la base de datos, *no* de una prueba)
        """
        self.assertTrue(self.bancos[0].preguntas.all()[
                        0].respuestas.all()[2].es_correcta)
        self.assertFalse(self.bancos[0].preguntas.all()[
                         0].respuestas.all()[0].es_correcta)

    def test_prueba_diagnostico_data(self):
        """
        Verificacion de los contenidos de una prueba recien generada
        """
        self.assertQuerysetEqual(self.diagnostico.preguntas.all(), [
                                 '<Pregunta: Cuanto es 9x9>', '<Pregunta: Cual es la raiz cuadrada de 16>', '<Pregunta: PI es un numero>'], ordered=False)
        self.assertIsNotNone(self.diagnostico.fecha_presentacion)
        self.assertEqual(self.diagnostico.resumen,
                         '1. Cuanto es 9x9\n - Resp: 81\n2. Cual es la raiz cuadrada de 16\n - Resp: 4\n3. PI es un numero\n - Resp: Trascendental e Irracional\n')

    def test_prueba_view_and_context(self):
        """
        Prueba para verficar el comportamiento esperado de la vista de presentacion de prueba, que use la plantilla esperada y que
        el formulario del contexto contenga las mismas preguntas trabajadas hasta ahora
        """
        c = Client()
        # probar que la URL sea reconocida
        self.assertEqual(
            reverse('diagnosticos:presentar-prueba'), '/pruebas/presentar/')
        # peticion con usuario anonimo
        response = c.get(
            reverse('diagnosticos:presentar-prueba'), banco=self.bancos[0])
        # probar que haya redireccionamiento
        self.assertEqual(response.status_code, 302)
        # Iniciamos sesion
        response = c.login(username=self.user.username, password='1234simple')
        # tratamos otra vez de presentar prueba
        response = c.get(
            reverse('diagnosticos:presentar-prueba'), banco=self.bancos[0])
        # tuvimos exito?
        self.assertEqual(response.status_code, 200)
        # verificamos que cargue la plantilla correcta
        self.assertTemplateUsed(response, 'diagnostico_presentar.html')
