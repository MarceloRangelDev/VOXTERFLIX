"""Testes de criação, edição, exclusão e limite de perfis."""

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.profiles.models import Profile


class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="carla", email="carla@exemplo.com", password="SenhaForte123!")
        self.client.force_login(self.user)

    def test_create_profile(self):
        response = self.client.post(reverse("profiles:criar"), {"name": "Carla", "avatar": "azul", "is_kids": ""})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Profile.objects.filter(user=self.user, name="Carla").exists())

    def test_create_kids_profile(self):
        self.client.post(reverse("profiles:criar"), {"name": "Criança", "avatar": "verde", "is_kids": "on"})
        profile = Profile.objects.get(user=self.user, name="Criança")
        self.assertTrue(profile.is_kids)

    def test_edit_profile(self):
        profile = Profile.objects.create(user=self.user, name="Original", avatar="azul")
        self.client.post(reverse("profiles:editar", args=[profile.id]), {"name": "Renomeado", "avatar": "roxo", "is_kids": ""})
        profile.refresh_from_db()
        self.assertEqual(profile.name, "Renomeado")
        self.assertEqual(profile.avatar, "roxo")

    def test_delete_profile(self):
        profile = Profile.objects.create(user=self.user, name="Remover", avatar="azul")
        self.client.post(reverse("profiles:excluir", args=[profile.id]))
        self.assertFalse(Profile.objects.filter(pk=profile.id).exists())

    @override_settings(MAX_PROFILES_PER_USER=2)
    def test_cannot_exceed_max_profiles(self):
        Profile.objects.create(user=self.user, name="Um", avatar="azul")
        Profile.objects.create(user=self.user, name="Dois", avatar="ciano")

        response = self.client.post(reverse("profiles:criar"), {"name": "Tres", "avatar": "verde", "is_kids": ""})

        self.assertEqual(response.status_code, 200)  # form volta com erro, não redireciona
        self.assertEqual(Profile.objects.filter(user=self.user).count(), 2)

    def test_activate_profile_sets_session(self):
        profile = Profile.objects.create(user=self.user, name="Ativo", avatar="azul")
        self.client.get(reverse("profiles:ativar", args=[profile.id]))
        self.assertEqual(self.client.session.get("active_profile_id"), profile.id)

    def test_cannot_activate_another_users_profile(self):
        other_user = User.objects.create_user(username="outro", email="outro@exemplo.com", password="x")
        other_profile = Profile.objects.create(user=other_user, name="Alheio", avatar="azul")
        response = self.client.get(reverse("profiles:ativar", args=[other_profile.id]))
        self.assertEqual(response.status_code, 404)
