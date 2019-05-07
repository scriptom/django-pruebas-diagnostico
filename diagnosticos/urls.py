from .views import DiagnosticoDetailView, PresentarView
from django.urls import path

app_name = 'diagnosticos'
urlpatterns = [
    path('presentar/', PresentarView.as_view(), name='presentar-prueba'),
    path('ver/<int:pk>/', DiagnosticoDetailView.as_view(), name='prueba-detalle'),
]