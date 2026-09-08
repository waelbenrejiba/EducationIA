from django.urls import path
from .views import ChatHistoryView

urlpatterns = [
    path("chat/history/<str:other_user_id>/", ChatHistoryView.as_view(), name="chat-history"),
]