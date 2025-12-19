from django.contrib import admin
from django.utils.html import format_html
from .models import Vacancy, SearchQuery


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ('name', 'employer_name', 'area', 'get_salary_display', 'published_at')
    list_filter = ('area', 'experience', 'employment', 'published_at')
    search_fields = ('name', 'employer_name', 'description')
    readonly_fields = ('hh_id', 'published_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'hh_id', 'area', 'published_at')
        }),
        ('Зарплата', {
            'fields': ('salary_from', 'salary_to', 'currency', 'salary_gross')
        }),
        ('Работодатель', {
            'fields': ('employer_name', 'employer_url')
        }),
        ('Описание', {
            'fields': ('description', 'key_skills')
        }),
        ('Требования', {
            'fields': ('experience', 'employment', 'schedule')
        }),
        ('Ссылки', {
            'fields': ('alternate_url',)
        }),
    )
    
    def get_salary_display(self, obj):
        return obj.get_salary_display()
    get_salary_display.short_description = 'Зарплата'


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ('query', 'area', 'experience', 'employment', 'search_date', 'results_count')
    list_filter = ('area', 'experience', 'employment', 'search_date')
    search_fields = ('query',)
    readonly_fields = ('search_date',)