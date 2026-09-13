"""Testes de favoritos: adicionar, remover, duplicidade e isolamento por perfil."""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.catalog.services.omdb import TitleDetail
from apps.favorites.models import Favorite
from apps.profiles.models import Profile

FAKE_DETAIL = TitleDetail(imdb_id="tt0111161", title="The Shawshank Redemption", year="1994", type="movie", poster="")


class FavoriteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dora", email="dora@exemplo.com", password="SenhaForte123!")
        self.profile = Profile.objects.create(user=self.user, name="Dora", avatar="azul")
        self.client.force_login(self.user)
        session = self.client.session
        session["active_profile_id"] = self.profile.id
        session.save()

    @patch("apps.favorites.views.OMDbService")
    def test_add_favorite(self, mock_omdb):
        mock_omdb.return_value.get_by_imdb_id.return_value = FAKE_DETAIL

        self.client.post(reverse("favorites:alternar", args=["tt0111161"]))

        self.assertTrue(Favorite.objects.filter(profile=self.profile, imdb_id="tt0111161").exists())

    @patch("apps.favorites.views.OMDbService")
    def test_toggle_removes_existing_favorite(self, mock_omdb):
        mock_omdb.return_value.get_by_imdb_id.return_value = FAKE_DETAIL
        Favorite.objects.create(profile=self.profile, imdb_id="tt0111161", title="The Shawshank Redemption")

        self.client.post(reverse("favorites:alternar", args=["tt0111161"]))

        self.assertFalse(Favorite.objects.filter(profile=self.profile, imdb_id="tt0111161").exists())

    def test_favorite_unique_per_profile(self):
        Favorite.objects.create(profile=self.profile, imdb_id="tt0111161", title="X")
        with self.assertRaises(Exception):
            Favorite.objects.create(profile=self.profile, imdb_id="tt0111161", title="X")

    def test_favorites_isolated_between_profiles(self):
        other_profile = Profile.objects.create(user=self.user, name="Outro", avatar="ciano")
        Favorite.objects.create(profile=self.profile, imdb_id="tt0111161", title="Filme Exclusivo Da Dora")

        response = self.client.get(reverse("favorites:lista"))
        self.assertContains(response, "Filme Exclusivo Da Dora")

        session = self.client.session
        session["active_profile_id"] = other_profile.id
        session.save()
        response = self.client.get(reverse("favorites:lista"))
        self.assertNotContains(response, "Filme Exclusivo Da Dora")
