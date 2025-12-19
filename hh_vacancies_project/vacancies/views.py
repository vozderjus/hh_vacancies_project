from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView
from .forms import SearchForm, ImportForm
from .services import HHApiService


class HomeView(TemplateView):
    """Главная страница"""
    template_name = 'vacancies/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm()
        context['import_form'] = ImportForm()
        return context


class VacancyListView(TemplateView):
    """Список вакансий"""
    template_name = 'vacancies/vacancy_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm(self.request.GET or None)
        return context


class VacancyDetailView(TemplateView):
    """Детали вакансии"""
    template_name = 'vacancies/vacancy_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vacancy_id'] = self.kwargs.get('hh_id')
        return context


class SearchView(TemplateView):
    """Поиск вакансий"""
    template_name = 'vacancies/search.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm(self.request.GET or None)
        return context


class ImportVacanciesView(TemplateView):
    """Импорт вакансий"""
    template_name = 'vacancies/import.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['import_form'] = ImportForm()
        return context
    
    def post(self, request, *args, **kwargs):
        form = ImportForm(request.POST)
        if form.is_valid():
            # Просто редирект для теста
            return redirect('vacancy_list')
        return self.render_to_response({'import_form': form})


class StatisticsView(TemplateView):
    """Статистика"""
    template_name = 'vacancies/statistics.html'


def api_search(request):
    """API для поиска"""
    return {'status': 'ok', 'message': 'API работает'}