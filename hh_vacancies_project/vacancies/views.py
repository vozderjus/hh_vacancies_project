from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count, Avg, Max, Min
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from datetime import datetime, timedelta
import json

from .models import Vacancy, SearchQuery
from .forms import SearchForm, ImportForm
from .services import HHApiService


class HomeView(TemplateView):
    """Главная страница"""
    template_name = 'vacancies/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Статистика для главной страницы
        context['total_vacancies'] = Vacancy.objects.count()
        
        # Количество уникальных работодателей
        context['total_employers'] = Vacancy.objects.values('employer_name').distinct().count()
        
        # Средние зарплаты
        salary_stats = Vacancy.objects.filter(
            Q(salary_from__isnull=False) | Q(salary_to__isnull=False)
        ).aggregate(
            avg_from=Avg('salary_from'),
            avg_to=Avg('salary_to')
        )
        context['avg_salary_from'] = int(salary_stats['avg_from'] or 0)
        context['avg_salary_to'] = int(salary_stats['avg_to'] or 0)
        
        # Последние 6 вакансий
        context['recent_vacancies'] = Vacancy.objects.all().order_by('-published_at')[:6]
        
        return context


class VacancyListView(ListView):
    """Список всех вакансий с поиском и фильтрацией"""
    model = Vacancy
    template_name = 'vacancies/vacancy_list.html'
    context_object_name = 'vacancies'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Vacancy.objects.all()
        
        # Поиск по ключевым словам
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(key_skills__icontains=search_query) |
                Q(employer_name__icontains=search_query)
            )
        
        # Фильтры
        area = self.request.GET.get('area')
        if area:
            queryset = queryset.filter(area__icontains=area)
        
        experience = self.request.GET.get('experience')
        if experience:
            queryset = queryset.filter(experience__icontains=experience)
        
        employment = self.request.GET.get('employment')
        if employment:
            queryset = queryset.filter(employment__icontains=employment)
        
        # Фильтр по зарплате
        salary_from = self.request.GET.get('salary_from')
        if salary_from and salary_from.isdigit():
            queryset = queryset.filter(
                Q(salary_from__gte=int(salary_from)) | 
                Q(salary_to__gte=int(salary_from))
            )
        
        salary_to = self.request.GET.get('salary_to')
        if salary_to and salary_to.isdigit():
            queryset = queryset.filter(
                Q(salary_to__lte=int(salary_to)) | 
                Q(salary_from__lte=int(salary_to))
            )
        
        # Сортировка
        sort_by = self.request.GET.get('sort', '-published_at')
        if sort_by in ['-published_at', 'published_at', '-salary_from', 'salary_from', '-salary_to', 'salary_to']:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Форма поиска с текущими параметрами
        context['search_form'] = SearchForm(self.request.GET or None)
        
        # Общее количество отфильтрованных вакансий
        context['total_count'] = self.get_queryset().count()
        
        return context


class VacancyDetailView(DetailView):
    """Детальная информация о вакансии"""
    model = Vacancy
    template_name = 'vacancies/vacancy_detail.html'
    context_object_name = 'vacancy'
    
    def get_object(self, queryset=None):
        # Получаем вакансию по hh_id из URL
        hh_id = self.kwargs.get('hh_id')
        return get_object_or_404(Vacancy, hh_id=hh_id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Похожие вакансии (по тому же работодателю или похожему названию)
        vacancy = self.object
        
        # Разбиваем ключевые навыки
        if vacancy.key_skills:
            context['key_skills'] = [skill.strip() for skill in vacancy.key_skills.split(',') if skill.strip()]
        else:
            context['key_skills'] = []
        
        # Похожие вакансии
        similar_vacancies = Vacancy.objects.filter(
            Q(employer_name=vacancy.employer_name) |
            Q(name__icontains=vacancy.name.split()[0])
        ).exclude(id=vacancy.id)[:3]
        
        context['similar_vacancies'] = similar_vacancies
        
        return context


class SearchView(TemplateView):
    """Страница расширенного поиска"""
    template_name = 'vacancies/search.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Если есть параметры поиска, перенаправляем на список вакансий
        if self.request.GET.get('q'):
            return self.redirect_to_vacancy_list()
        
        # Инициализируем сервис API
        api_service = HHApiService()
        
        # Получаем данные для формы
        context['areas'] = api_service.get_areas()
        context['api_available'] = api_service.test_connection()
        
        # Форма поиска с текущими параметрами
        context['search_form'] = SearchForm(self.request.GET or None)
        
        return context
    
    def redirect_to_vacancy_list(self):
        """Перенаправление на страницу списка вакансий с параметрами поиска"""
        params = self.request.GET.copy()
        if 'page' in params:
            del params['page']
        
        redirect_url = f"/vacancies/?{params.urlencode()}"
        return redirect(redirect_url)
    
    def post(self, request, *args, **kwargs):
        """Обработка формы поиска (POST запрос)"""
        form = SearchForm(request.POST)
        
        if form.is_valid():
            # Сохраняем поисковый запрос в историю
            search_data = form.cleaned_data
            
            SearchQuery.objects.create(
                query=search_data.get('query', ''),
                area=search_data.get('area', ''),
                experience=search_data.get('experience', ''),
                employment=search_data.get('employment', ''),
                results_count=0  # Будет обновлено после поиска
            )
            
            # Формируем URL для редиректа
            params = {}
            if search_data.get('query'):
                params['q'] = search_data['query']
            if search_data.get('area'):
                params['area'] = search_data['area']
            if search_data.get('experience'):
                params['experience'] = search_data['experience']
            if search_data.get('employment'):
                params['employment'] = search_data['employment']
            if search_data.get('salary_from'):
                params['salary_from'] = search_data['salary_from']
            if search_data.get('salary_to'):
                params['salary_to'] = search_data['salary_to']
            if search_data.get('sort_by'):
                params['sort'] = search_data['sort_by']
            
            redirect_url = f"/vacancies/"
            if params:
                redirect_url += f"?{ '&'.join([f'{k}={v}' for k, v in params.items() if v]) }"
            
            return redirect(redirect_url)
        
        # Если форма не валидна, показываем ошибки
        context = self.get_context_data()
        context['search_form'] = form
        return self.render_to_response(context)


class ImportVacanciesView(TemplateView):
    """Импорт вакансий с HH API"""
    template_name = 'vacancies/import.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Инициализируем сервис API
        api_service = HHApiService()
        
        # Получаем данные для формы
        context['areas'] = api_service.get_areas()
        context['api_available'] = api_service.test_connection()
        
        # Форма импорта
        context['import_form'] = ImportForm()
        
        # История импортов (последние 10)
        context['recent_imports'] = SearchQuery.objects.all().order_by('-search_date')[:10]
        
        return context
    
    def post(self, request, *args, **kwargs):
        form = ImportForm(request.POST)
        
        if form.is_valid():
            search_query = form.cleaned_data['search_query']
            count = min(form.cleaned_data['count'], 50)  # Ограничиваем 50
            area = form.cleaned_data.get('area', '113')
            
            # Подготавливаем параметры для API
            search_params = {
                'text': search_query,
                'per_page': count,
                'area': area,
                'order_by': 'relevance'
            }
            
            # Добавляем дополнительные фильтры из формы
            experience = request.POST.get('experience')
            if experience:
                search_params['experience'] = experience
            
            # Импортируем вакансии
            api_service = HHApiService()
            
            # Проверяем доступность API
            if not api_service.test_connection():
                messages.error(request, "❌ HH API недоступно. Проверьте подключение к интернету.")
                return self.render_to_response(self.get_context_data())
            
            # Показываем сообщение о начале импорта
            messages.info(request, f"⏳ Начинаем импорт вакансий по запросу: '{search_query}'...")
            
            # Запускаем импорт
            result = api_service.import_vacancies(search_params)
            
            if result['success']:
                messages.success(
                    request,
                    f"✅ Успешно импортировано {result['count']} вакансий"
                )
                
                if result.get('errors'):
                    for error in result['errors'][:3]:  # Показываем только 3 ошибки
                        messages.warning(request, f"⚠️ {error}")
                        
            else:
                messages.error(request, f"❌ Ошибка импорта: {result.get('message', 'Неизвестная ошибка')}")
            
            return redirect('import_vacancies')
        
        # Если форма не валидна
        context = self.get_context_data()
        context['import_form'] = form
        return self.render_to_response(context)


class StatisticsView(TemplateView):
    """Статистика по вакансиям"""
    template_name = 'vacancies/statistics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Основная статистика
        context['total_vacancies'] = Vacancy.objects.count()
        context['total_employers'] = Vacancy.objects.values('employer_name').distinct().count()
        
        # Статистика по зарплате
        salary_stats = Vacancy.objects.aggregate(
            avg_salary_from=Avg('salary_from'),
            avg_salary_to=Avg('salary_to'),
            max_salary=Max('salary_to'),
            min_salary=Min('salary_from')
        )
        context['salary_stats'] = salary_stats
        
        # Статистика по опыту
        experience_stats = Vacancy.objects.values('experience').annotate(
            count=Count('id')
        ).order_by('-count')
        context['experience_stats'] = experience_stats
        
        # Статистика по регионам
        area_stats = Vacancy.objects.values('area').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        context['area_stats'] = area_stats
        
        # Топ работодателей
        top_employers = Vacancy.objects.values('employer_name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        context['top_employers'] = top_employers
        
        # Популярные навыки
        all_skills = []
        vacancies = Vacancy.objects.exclude(key_skills='')
        for vacancy in vacancies:
            if vacancy.key_skills:
                skills = [s.strip() for s in vacancy.key_skills.split(',') if s.strip()]
                all_skills.extend(skills)
        
        from collections import Counter
        skill_counter = Counter(all_skills)
        popular_skills = skill_counter.most_common(15)
        context['popular_skills'] = popular_skills
        
        return context


# API Views для AJAX запросов
def api_vacancy_search(request):
    """API для быстрого поиска вакансий (AJAX)"""
    if request.method == 'GET':
        query = request.GET.get('q', '').strip()
        limit = int(request.GET.get('limit', 10))
        
        if len(query) < 2:
            return JsonResponse({'items': [], 'count': 0})
        
        vacancies = Vacancy.objects.filter(
            Q(name__icontains=query) |
            Q(employer_name__icontains=query) |
            Q(key_skills__icontains=query)
        ).order_by('-published_at')[:limit]
        
        results = []
        for vacancy in vacancies:
            results.append({
                'id': vacancy.id,
                'hh_id': vacancy.hh_id,
                'name': vacancy.name,
                'employer': vacancy.employer_name,
                'area': vacancy.area,
                'salary': f"{vacancy.salary_from or ''}-{vacancy.salary_to or ''} {vacancy.currency or '₽'}",
                'url': f"/vacancies/{vacancy.hh_id}/",
                'published_at': vacancy.published_at.strftime('%d.%m.%Y')
            })
        
        return JsonResponse({
            'items': results,
            'count': len(results),
            'query': query
        })
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


def api_get_statistics(request):
    """API для получения статистики"""
    stats = {
        'total_vacancies': Vacancy.objects.count(),
        'total_employers': Vacancy.objects.values('employer_name').distinct().count(),
        'avg_salary': int(Vacancy.objects.filter(
            salary_from__isnull=False
        ).aggregate(avg=Avg('salary_from'))['avg'] or 0),
        'recent_imports': SearchQuery.objects.count(),
        'last_import': SearchQuery.objects.order_by('-search_date').first().search_date.strftime('%d.%m.%Y %H:%M') 
            if SearchQuery.objects.exists() else 'Нет данных'
    }
    return JsonResponse(stats)


def clear_database(request):
    """Очистка базы данных (только для разработки)"""
    if request.method == 'POST' and request.user.is_superuser:
        Vacancy.objects.all().delete()
        SearchQuery.objects.all().delete()
        messages.success(request, "✅ База данных успешно очищена")
        return redirect('home')
    
    return redirect('home')


def test_api_view(request):
    """Тестирование подключения к HH API"""
    api_service = HHApiService()
    is_available = api_service.test_connection()
    
    if request.method == 'POST':
        query = request.POST.get('query', 'Python')
        params = {
            'text': query,
            'per_page': 5,
            'area': '113'
        }
        
        result = api_service.search_vacancies(params)
        
        if result.get('items'):
            messages.success(request, f"✅ API работает! Найдено {result.get('found', 0)} вакансий по запросу '{query}'")
        else:
            messages.warning(request, "⚠️ API вернуло пустой результат")
        
        return redirect('test_api')
    
    context = {
        'api_available': is_available,
        'test_result': None
    }
    
    return render(request, 'vacancies/test_api.html', context)