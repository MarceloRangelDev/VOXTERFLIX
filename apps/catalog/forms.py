"""Formulário de busca avançada do catálogo.

Importante: a OMDb API só permite buscar por título (`s=`) ou por ID
(`i=`), com filtro nativo apenas de `type` e `y` (ano exato). Não existe
endpoint de "buscar por gênero/ator/diretor/nota". Por isso, quando o
usuário usa esses filtros avançados, o VoxterFlixbusca por título na OMDb
e depois refina o resultado no backend (ver `apps/catalog/views.py`).
Essa limitação está documentada no README.
"""

from django import forms

CURRENT_YEAR = 2026

GENRE_CHOICES = [
    ("", "Todos os gêneros"),
    ("Action", "Ação"),
    ("Comedy", "Comédia"),
    ("Drama", "Drama"),
    ("Sci-Fi", "Ficção científica"),
    ("Horror", "Terror"),
    ("Animation", "Animação"),
    ("Romance", "Romance"),
    ("Adventure", "Aventura"),
    ("Thriller", "Suspense"),
    ("Documentary", "Documentário"),
    ("Crime", "Crime"),
    ("Fantasy", "Fantasia"),
]

TYPE_CHOICES = [
    ("", "Filmes e séries"),
    ("movie", "Filmes"),
    ("series", "Séries"),
]

SORT_CHOICES = [
    ("relevance", "Relevância"),
    ("year_desc", "Ano (mais recente)"),
    ("year_asc", "Ano (mais antigo)"),
    ("rating_desc", "Nota IMDb (maior)"),
    ("rating_asc", "Nota IMDb (menor)"),
]


class AdvancedSearchForm(forms.Form):
    """Todos os campos são opcionais exceto `q`, exigido pela própria OMDb."""

    q = forms.CharField(
        label="Título",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Busque por título..."}),
    )
    type = forms.ChoiceField(label="Tipo", choices=TYPE_CHOICES, required=False)
    genre = forms.ChoiceField(label="Gênero", choices=GENRE_CHOICES, required=False)
    year_from = forms.IntegerField(label="Ano inicial", required=False, min_value=1900, max_value=CURRENT_YEAR + 1)
    year_to = forms.IntegerField(label="Ano final", required=False, min_value=1900, max_value=CURRENT_YEAR + 1)
    rating_min = forms.FloatField(label="Nota IMDb mínima", required=False, min_value=0, max_value=10)
    rating_max = forms.FloatField(label="Nota IMDb máxima", required=False, min_value=0, max_value=10)
    country = forms.CharField(label="País", max_length=60, required=False)
    language = forms.CharField(label="Idioma", max_length=60, required=False)
    rated = forms.CharField(label="Classificação indicativa", max_length=20, required=False)
    actor = forms.CharField(label="Ator", max_length=80, required=False)
    director = forms.CharField(label="Diretor", max_length=80, required=False)
    sort = forms.ChoiceField(label="Ordenar por", choices=SORT_CHOICES, required=False, initial="relevance")
    page = forms.IntegerField(required=False, min_value=1, max_value=100, initial=1)

    def clean(self):
        """Valida no backend mesmo que os valores venham de query params da URL."""
        cleaned = super().clean()
        year_from = cleaned.get("year_from")
        year_to = cleaned.get("year_to")
        if year_from and year_to and year_from > year_to:
            cleaned["year_from"], cleaned["year_to"] = year_to, year_from

        rating_min = cleaned.get("rating_min")
        rating_max = cleaned.get("rating_max")
        if rating_min is not None and rating_max is not None and rating_min > rating_max:
            cleaned["rating_min"], cleaned["rating_max"] = rating_max, rating_min

        return cleaned

    def has_advanced_filters(self) -> bool:
        """Indica se algum filtro que exige buscar detalhes (N+1) foi usado."""
        advanced_fields = ["genre", "year_from", "year_to", "rating_min", "rating_max", "country", "language", "rated", "actor", "director"]
        return any(self.cleaned_data.get(field) for field in advanced_fields)
