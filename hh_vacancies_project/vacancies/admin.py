from django.contrib import admin
from .models import Vacancy, SearchQuery


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ('name', 'employer_name', 'area', 'published_at')
    list_filter = ('area', 'published_at')
    search_fields = ('name', 'employer_name')


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ('query', 'search_date', 'results_count')
    list_filter = ('search_date',)
    search_fields = ('query',)