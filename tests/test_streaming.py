"""Testes do player: validação de IMDb ID, autorização e indisponibilidade."""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.catalog.services.omdb import TitleDetail
from apps.profiles.models import Profile
from apps.streaming.services.superflix import InvalidPlaybackRequestError, SuperFlixService

FAKE_MOVIE = TitleDetail(imdb_id="tt0111161", title="Shawshank", year="1994", type="movie", poster="", rated="R", genre="Drama")


class SuperFlixServiceTests(TestCase):
    @override_settings(SUPERFLIX_API_BASE_URL="")
    def test_not_configured_raises(self):
        service = SuperFlixService()
        self.assertFalse(service.is_configured())

    @override_settings(SUPERFLIX_API_BASE_URL="https://exemplo-superflix.test")
    def test_builds_movie_url(self):
        service = SuperFlixService()
        source = service.build_movie_source("tt0111161")
        self.assertEqual(source.embed_url, "https://exemplo-superflix.test/filme/tt0111161")

    @override_settings(SUPERFLIX_API_BASE_URL="https://exemplo-superflix.test")
    def test_builds_episode_url(self):
        service = SuperFlixService()
        source = service.build_episode_source("tt0903747", 1, 3)
        self.assertEqual(source.embed_url, "https://exemplo-superflix.test/serie/tt0903747/1/3")

    def test_rejects_invalid_imdb_id(self):
        service = SuperFlixService()
        with self.assertRaises(InvalidPlaybackRequestError):
            service.build_movie_source("<script>alert(1)</script>")

    @override_settings(SUPERFLIX_API_BASE_URL="https://exemplo-superflix.test")
    def test_rejects_invalid_episode_number(self):
        service = SuperFlixService()
        with self.assertRaises(InvalidPlaybackRequestError):
            service.build_episode_source("tt0903747", 0, 1)


class PlayerViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="leo", email="leo@exemplo.com", password="SenhaForte123!")
        self.profile = Profile.objects.create(user=self.user, name="Leo", avatar="azul")
        self.client.force_login(self.user)
        session = self.client.session
        session["active_profile_id"] = self.profile.id
        session.save()

    @override_settings(SUPERFLIX_API_BASE_URL="")
    @patch("apps.streaming.views.OMDbService")
    def test_shows_friendly_message_when_not_configured(self, mock_service_class):
        mock_service_class.return_value.get_by_imdb_id.return_value = FAKE_MOVIE
        response = self.client.get(reverse("streaming:assistir_filme", args=["tt0111161"]))
        self.assertContains(response, "ainda não está configurado")

    @override_settings(SUPERFLIX_API_BASE_URL="https://exemplo-superflix.test")
    @patch("apps.streaming.views.OMDbService")
    def test_kids_profile_denied_for_r_rated(self, mock_service_class):
        mock_service_class.return_value.get_by_imdb_id.return_value = FAKE_MOVIE
        kids_profile = Profile.objects.create(user=self.user, name="Kids", avatar="verde", is_kids=True)
        session = self.client.session
        session["active_profile_id"] = kids_profile.id
        session.save()

        response = self.client.get(reverse("streaming:assistir_filme", args=["tt0111161"]))

        self.assertContains(response, "não está disponível no perfil infantil")

    def test_invalid_imdb_id_format_returns_404(self):
        response = self.client.get("/streaming/assistir/not-an-id/")
        self.assertEqual(response.status_code, 404)
