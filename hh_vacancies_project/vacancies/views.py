from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.contrib import messages
from django.views.generic import ListView, DetailView, TemplateView
from django.http import JsonResponse
from .models import Vacancy, SearchQuery
from .forms import SearchForm, ImportForm
from .services import HHApiService


class HomeView(TemplateView):
    """Главная страница"""
    template_name = 'vacancies/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm()
        context['import_form'] = ImportForm()
        context['recent_vacancies'] = Vacancy.objects.all()[:5]
        return context


class VacancyListView(ListView):
    """Список всех вакансий"""
    model = Vacancy
    template_name = 'vacancies/vacancy_list.html'
    context_object_name = 'vacancies'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фильтрация по поисковому запросу
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(key_skills__icontains=search_query) |
                Q(employer_name__icontains=search_query)
            )
        
        # Фильтрация по опыту
        experience = self.request.GET.get('experience')
        if experience:
            queryset = queryset.filter(experience__icontains=experience)
        
        # Фильтрация по типу занятости
        employment = self.request.GET.get('employment')
        if employment:
            queryset = queryset.filter(employment__icontains=employment)
        
        # Фильтрация по региону
        area = self.request.GET.get('area')
        if area:
            queryset = queryset.filter(area__icontains=area)
        
        # Фильтрация по зарплате
        salary_from = self.request.GET.get('salary_from')
        salary_to = self.request.GET.get('salary_to')
        
        if salary_from:
            queryset = queryset.filter(
                Q(salary_from__gte=salary_from) | Q(salary_to__gte=salary_from)
            )
        
        if salary_to:
            queryset = queryset.filter(
                Q(salary_to__lte=salary_to) | Q(salary_from__lte=salary_to)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm(self.request.GET or None)
        context['total_count'] = Vacancy.objects.count()
        context['filtered_count'] = self.get_queryset().count()
        return context


class VacancyDetailView(DetailView):
    """Детальная информация о вакансии"""
    model = Vacancy
    template_name = 'vacancies/vacancy_detail.html'
    context_object_name = 'vacancy'
    
    def get_object(self, queryset=None):
        return get_object_or_404(Vacancy, hh_id=self.kwargs.get('hh_id'))


class SearchView(TemplateView):
    """Страница поиска вакансий"""
    template_name = 'vacancies/search.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm(self.request.GET or None)
        context['popular_filters'] = HHApiService.get_popular_filters()
        return context
    
    def post(self, request, *args, **kwargs):
        form = SearchForm(request.POST)
        
        if form.is_valid():
            # Сохраняем поисковый запрос в истории
            search_query = SearchQuery.objects.create(
                query=form.cleaned_data.get('query', ''),
                area=form.cleaned_data.get('area'),
                experience=form.cleaned_data.get('experience'),
                employment=form.cleaned_data.get('employment')
            )
            
            # Формируем URL для перенаправления с параметрами поиска
            params = []
            for key, value in form.cleaned_data.items():
                if value:
                    params.append(f"{key}={value}")
            
            redirect_url = f"/vacancies/"
            if params:
                redirect_url += f"?{'&'.join(params)}"
            
            return redirect(redirect_url)
        
        return self.render_to_response({'search_form': form})


class ImportVacanciesView(TemplateView):
    """Импорт вакансий с HH API"""
    template_name = 'vacancies/import.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['import_form'] = ImportForm()
        return context
    
    def post(self, request, *args, **kwargs):
        form = ImportForm(request.POST)
        
        if form.is_valid():
            search_query = form.cleaned_data['search_query']
            count = form.cleaned_data['count']
            
            # Параметры для поиска в API
            search_params = {
                "search_text": search_query,
                "per_page": min(count, 50),  # Максимум 50 за один запрос
                "area": "113",  # Вся Россия
            }
            
            try:
                # Импортируем вакансии
                saved_vacancies = HHApiService.save_vacancies_from_api(search_params)
                
                messages.success(
                    request,
                    f"Успешно импортировано {len(saved_vacancies)} вакансий по запросу '{search_query}'"
                )
                
                return redirect('vacancy_list')
            
            except Exception as e:
                messages.error(request, f"Ошибка при импорте вакансий: {str(e)}")
        
        return self.render_to_response({'import_form': form})


class StatisticsView(TemplateView):
    """Статистика по вакансиям"""
    template_name = 'vacancies/statistics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Основная статистика
        total_vacancies = Vacancy.objects.count()
        
        # Статистика по опыту
        experience_stats = Vacancy.objects.values('experience').annotate(
            count=models.Count('id')
        ).order_by('-count')
        
        # Статистика по типу занятости
        employment_stats = Vacancy.objects.values('employment').annotate(
            count=models.Count('id')
        ).order_by('-count')
        
        # Топ-10 работодателей
        top_employers = Vacancy.objects.values('employer_name').annotate(
            count=models.Count('id')
        ).order_by('-count')[:10]
        
        # Средняя зарплата
        vacancies_with_salary = Vacancy.objects.exclude(
            Q(salary_from__isnull=True) & Q(salary_to__isnull=True)
        )
        
        avg_salary_from = vacancies_with_salary.aggregate(
            avg=models.Avg('salary_from')
        )['avg'] or 0
        
        avg_salary_to = vacancies_with_salary.aggregate(
            avg=models.Avg('salary_to')
        )['avg'] or 0
        
        context.update({
            'total_vacancies': total_vacancies,
            'experience_stats': experience_stats,
            'employment_stats': employment_stats,
            'top_employers': top_employers,
            'avg_salary_from': int(avg_salary_from),
            'avg_salary_to': int(avg_salary_to),
        })
        
        return context


def api_search(request):
    """API endpoint для поиска вакансий (для AJAX)"""
    if request.method == 'GET':
        query = request.GET.get('q', '')
        area = request.GET.get('area', '1')
        
        if query:
            vacancies_data = HHApiService.get_vacancies(
                search_text=query,
                area=area,
                per_page=10
            )
            
            return JsonResponse(vacancies_data)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)