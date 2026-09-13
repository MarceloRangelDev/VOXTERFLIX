"""Testes de busca, detalhes e tratamento de erros da integração com a OMDb."""

from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from apps.catalog.services.omdb import (
    OMDbNotFoundError,
    OMDbService,
    TitleDetail,
    TitleSummary,
)
from apps.profiles.models import Profile

FAKE_MOVIE = TitleDetail(
    imdb_id="tt0111161",
    title="The Shawshank Redemption",
    year="1994",
    type="movie",
    poster="",
    rated="R",
    genre="Drama",
    imdb_rating="9.3",
)


class LoggedInTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="rita", email="rita@exemplo.com", password="SenhaForte123!")
        self.profile = Profile.objects.create(user=self.user, name="Rita", avatar="azul")
        self.client.force_login(self.user)
        session = self.client.session
        session["active_profile_id"] = self.profile.id
        session.save()


class SearchViewTests(LoggedInTestCase):
    def test_search_requires_active_profile(self):
        session = self.client.session
        del session["active_profile_id"]
        session.save()
        response = self.client.get(reverse("catalog:buscar"), {"q": "batman"})
        self.assertRedirects(response, reverse("profiles:selecionar"))

    @patch("apps.catalog.views.OMDbService")
    def test_search_returns_results(self, mock_service_class):
        mock_service_class.return_value.search.return_value = (
            [TitleSummary(imdb_id="tt0111161", title="The Shawshank Redemption", year="1994", type="movie", poster="")],
            1,
        )
        response = self.client.get(reverse("catalog:buscar"), {"q": "shawshank"})
        self.assertContains(response, "The Shawshank Redemption")

    @patch("apps.catalog.views.OMDbService")
    def test_search_handles_not_found_gracefully(self, mock_service_class):
        mock_service_class.return_value.search.side_effect = OMDbNotFoundError("Movie not found!")
        response = self.client.get(reverse("catalog:buscar"), {"q": "titulo-inexistente-xyz"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nenhum resultado encontrado")


class DetailViewTests(LoggedInTestCase):
    @patch("apps.catalog.views.OMDbService")
    def test_detail_view_renders_title(self, mock_service_class):
        mock_service_class.return_value.get_by_imdb_id.return_value = FAKE_MOVIE
        response = self.client.get(reverse("catalog:detalhe", args=["tt0111161"]))
        self.assertContains(response, "The Shawshank Redemption")

    @patch("apps.catalog.views.OMDbService")
    def test_kids_profile_is_blocked_from_r_rated_title(self, mock_service_class):
        mock_service_class.return_value.get_by_imdb_id.return_value = FAKE_MOVIE
        kids_profile = Profile.objects.create(user=self.user, name="Kids", avatar="verde", is_kids=True)
        session = self.client.session
        session["active_profile_id"] = kids_profile.id
        session.save()

        response = self.client.get(reverse("catalog:detalhe", args=["tt0111161"]), follow=True)

        self.assertContains(response, "não está disponível no perfil infantil")


class OMDbServiceTests(TestCase):
    def setUp(self):
        cache.clear()

    @patch("apps.catalog.services.omdb.requests.get")
    def test_get_by_imdb_id_raises_not_found(self, mock_get):
        mock_get.return_value = Mock(status_code=200, json=lambda: {"Response": "False", "Error": "Incorrect IMDb ID."})
        service = OMDbService()
        service.api_key = "chave-de-teste"
        with self.assertRaises(Exception):
            service.get_by_imdb_id("tt0000000")

    @patch("apps.catalog.services.omdb.requests.get")
    def test_search_parses_results(self, mock_get):
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {
                "Response": "True",
                "Search": [{"imdbID": "tt0111161", "Title": "Shawshank", "Year": "1994", "Type": "movie", "Poster": "N/A"}],
                "totalResults": "1",
            },
        )
        service = OMDbService()
        service.api_key = "chave-de-teste"
        results, total = service.search("shawshank")
        self.assertEqual(total, 1)
        self.assertEqual(results[0].poster, "")  # "N/A" deve virar string vazia
