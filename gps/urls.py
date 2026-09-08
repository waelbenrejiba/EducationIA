from django.urls import path
from .views import UpdateLocationView, SupervisorEnfantsLocationView

urlpatterns = [
    path('update/', UpdateLocationView.as_view(), name='gps-update'),
    path('enfants-positions/', SupervisorEnfantsLocationView.as_view(), name='gps-enfants'),
]