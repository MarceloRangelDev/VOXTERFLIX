"""Comando de gerenciamento: popula as categorias e títulos curados iniciais.

A OMDb não tem endpoint de "populares" ou "em alta" (ver `services/omdb.py`),
então o VoxterFlix precisa de uma curadoria própria de quais IDs do IMDb
aparecem em cada carrossel da Home. Este comando cria esse conjunto inicial
com títulos reais e amplamente conhecidos, para que o catálogo já apareça
preenchido logo após a instalação.

Uso:
    python manage.py seed_catalog
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Category, CuratedTitle

CATALOGO_INICIAL = {
    "em-alta": {
        "name": "Em alta",
        "order": 0,
        "is_kids_allowed": True,
        "titles": ["tt6751668", "tt4154796", "tt0816692", "tt4574334", "tt2306299", "tt7366338"],
    },
    "filmes-populares": {
        "name": "Filmes populares",
        "order": 1,
        "is_kids_allowed": True,
        "titles": ["tt0468569", "tt1375666", "tt0133093", "tt0109830", "tt0110912", "tt0068646"],
    },
    "series-populares": {
        "name": "Séries populares",
        "order": 2,
        "is_kids_allowed": True,
        "titles": ["tt0903747", "tt0944947", "tt0386676", "tt1520211", "tt0141842", "tt2861424"],
    },
    "mais-bem-avaliados": {
        "name": "Mais bem avaliados",
        "order": 3,
        "is_kids_allowed": True,
        "titles": ["tt0111161", "tt0068646", "tt0071562", "tt0108052", "tt6751668", "tt0120737"],
    },
    "acao": {
        "name": "Ação",
        "order": 4,
        "is_kids_allowed": True,
        "titles": ["tt0468569", "tt1375666", "tt0167260", "tt0120815", "tt0060196", "tt0088247"],
    },
    "comedia": {
        "name": "Comédia",
        "order": 5,
        "is_kids_allowed": True,
        "titles": ["tt0107048", "tt0088763", "tt0119217", "tt0332280", "tt0993846"],
    },
    "drama": {
        "name": "Drama",
        "order": 6,
        "is_kids_allowed": True,
        "titles": ["tt0111161", "tt0109830", "tt0068646", "tt6751668", "tt2582802"],
    },
    "ficcao-cientifica": {
        "name": "Ficção científica",
        "order": 7,
        "is_kids_allowed": True,
        "titles": ["tt0816692", "tt0133093", "tt1375666", "tt0083658", "tt2543164", "tt0470752"],
    },
    "terror": {
        "name": "Terror",
        "order": 8,
        "is_kids_allowed": False,
        "titles": ["tt0078748", "tt0070047", "tt0081505", "tt5052448", "tt6644200"],
    },
    "animacao": {
        "name": "Animação",
        "order": 9,
        "is_kids_allowed": True,
        "titles": ["tt0114709", "tt2380307", "tt2948356", "tt4633694", "tt0910970", "tt1049413"],
    },
}


class Command(BaseCommand):
    help = "Cria as categorias e títulos curados iniciais do catálogo VoxterFlix."

    @transaction.atomic
    def handle(self, *args, **options):
        total_categorias = 0
        total_titulos = 0

        for slug, dados in CATALOGO_INICIAL.items():
            category, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": dados["name"],
                    "order": dados["order"],
                    "is_kids_allowed": dados["is_kids_allowed"],
                },
            )
            total_categorias += 1

            for posicao, imdb_id in enumerate(dados["titles"]):
                _, criado = CuratedTitle.objects.update_or_create(
                    category=category,
                    imdb_id=imdb_id,
                    defaults={"order": posicao, "is_featured": posicao == 0 and slug == "em-alta"},
                )
                if criado:
                    total_titulos += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Catálogo inicial criado/atualizado: {total_categorias} categorias, {total_titulos} títulos novos."
            )
        )
