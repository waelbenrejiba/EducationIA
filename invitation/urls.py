from django.urls import path
from .views import InvitationSendView, InvitationInboxView, InvitationRespondView, FriendsListView

urlpatterns = [
    path("invitations/send/", InvitationSendView.as_view(), name="invitation-send"),
    path("invitations/inbox/", InvitationInboxView.as_view(), name="invitation-inbox"),
    path("invitations/<int:invitation_id>/<str:action>/", InvitationRespondView.as_view(), name="invitation-respond"),
    path("friends/", FriendsListView.as_view(), name="friends-list"),
]