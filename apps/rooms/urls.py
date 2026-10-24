from django.urls import path
from . import views

app_name = "rooms"

urlpatterns = [
    path("", views.lobby, name="lobby"),
    path("create/", views.create_room, name="create_room"),
    path("join/", views.join_room, name="join_room"),
    path("room/<uuid:room_id>/", views.room_detail, name="room_detail"),
    path("room/<uuid:room_id>/end/", views.end_room, name="end_room"),
    path("test-gemini/", views.test_gemini, name="test_gemini"),
]