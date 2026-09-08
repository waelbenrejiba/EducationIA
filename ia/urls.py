from django.urls import path
from .views import GenererConseilsPsyView

urlpatterns = [
    path('conseils-psy/', GenererConseilsPsyView.as_view(), name='conseils_psy'),
]