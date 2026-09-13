"""Modelos de curadoria do catálogo.

A OMDb API não oferece endpoints de "em alta" ou "por gênero" — apenas
busca por título/ID (ver `apps/catalog/services/omdb.py`). Por isso o
VoxterFlix mantém sua própria curadoria: uma lista de IDs do IMDb por
categoria, usada para montar a Home e os carrosséis. Os *dados* de cada
título (poster, sinopse, nota) continuam vindo sempre da OMDb — nunca são
inventados ou copiados aqui.
"""

from django.db import models

from apps.core.models import TimestampedModel


class Category(TimestampedModel):
    """Uma categoria/carrossel exibido na Home (ex.: "Ação", "Em alta")."""

    name = models.CharField("nome", max_length=60)
    slug = models.SlugField("slug", unique=True)
    order = models.PositiveIntegerField("ordem de exibição", default=0)
    is_kids_allowed = models.BooleanField("permitido para perfil infantil", default=True)

    class Meta:
        verbose_name = "categoria"
        verbose_name_plural = "categorias"
        ordering = ["order", "name"]

    def __str__(self) -> str:
        return self.name


class CuratedTitle(TimestampedModel):
    """Um título (IMDb ID) curado para aparecer em uma categoria específica."""

    category = models.ForeignKey(Category, verbose_name="categoria", related_name="titles", on_delete=models.CASCADE)
    imdb_id = models.CharField("IMDb ID", max_length=20)
    order = models.PositiveIntegerField("ordem no carrossel", default=0)
    is_featured = models.BooleanField("destaque no banner principal", default=False)

    class Meta:
        verbose_name = "título curado"
        verbose_name_plural = "títulos curados"
        ordering = ["category__order", "order"]
        constraints = [
            models.UniqueConstraint(fields=["category", "imdb_id"], name="titulo_unico_por_categoria"),
        ]

    def __str__(self) -> str:
        return f"{self.imdb_id} em {self.category.name}"
