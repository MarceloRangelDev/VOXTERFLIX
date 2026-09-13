from django.urls import path, re_path

from apps.streaming import views

app_name = "streaming"

urlpatterns = [
    re_path(r"^assistir/(?P<imdb_id>tt\d{6,9})/$", views.play_movie, name="assistir_filme"),
    re_path(
        r"^assistir/(?P<imdb_id>tt\d{6,9})/(?P<season>\d+)/(?P<episode>\d+)/$",
        views.play_episode,
        name="assistir_episodio",
    ),
]
