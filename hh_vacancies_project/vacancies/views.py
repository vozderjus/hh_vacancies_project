from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count, Avg, Max, Min
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
import json
from datetime import datetime, timedelta

from .models import Vacancy, SearchQuery
from .forms import SearchForm, ImportForm
from .services import HHApiService


class HomeView(TemplateView):
    """Главная страница с реальными данными"""
    template_name = 'vacancies/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'HH Вакансии - Поиск работы'
        
        # Статистика для главной страницы
        context['total_vacancies'] = Vacancy.objects.count()
        context['total_employers'] = Vacancy.objects.values('employer_name').distinct().count()
        
        # Последние вакансии
        context['recent_vacancies'] = Vacancy.objects.all().order_by('-published_at')[:6]
        
        # Популярные навыки
        context['popular_skills'] = self.get_popular_skills(limit=8)
        
        # Средняя зарплата
        avg_salary = Vacancy.objects.filter(
            Q(salary_from__isnull=False) | Q(salary_to__isnull=False)
        ).aggregate(
            avg_from=Avg('salary_from'),
            avg_to=Avg('salary_to')
        )
        context['avg_salary_from'] = int(avg_salary['avg_from'] or 0)
        context['avg_salary_to'] = int(avg_salary['avg_to'] or 0)
        
        context['search_form'] = SearchForm()
        context['import_form'] = ImportForm()
        
        return context
    
    def get_popular_skills(self, limit=10):
        """Получение популярных навыков"""
        from collections import Counter
        all_skills = []
        
        vacancies = Vacancy.objects.exclude(key_skills='')
        for vacancy in vacancies:
            skills = [s.strip() for s in vacancy.key_skills.split(',') if s.strip()]
            all_skills.extend(skills)
        
        skill_counter = Counter(all_skills)
        return skill_counter.most_common(limit)


class VacancyListView(ListView):
    """Список вакансий с реальными данными и фильтрацией"""
    model = Vacancy
    template_name = 'vacancies/vacancy_list.html'
    context_object_name = 'vacancies'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = Vacancy.objects.all()
        
        # Поиск по тексту
        search_text = self.request.GET.get('q', '').strip()
        if search_text:
            queryset = queryset.filter(
                Q(name__icontains=search_text) |
                Q(description__icontains=search_text) |
                Q(key_skills__icontains=search_text) |
                Q(employer_name__icontains=search_text)
            )
        
        # Фильтр по региону
        area = self.request.GET.get('area')
        if area:
            queryset = queryset.filter(area__icontains=area)
        
        # Фильтр по опыту
        experience = self.request.GET.get('experience')
        if experience:
            queryset = queryset.filter(experience__icontains=experience)
        
        # Фильтр по занятости
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
        if sort_by in ['-published_at', 'published_at', 'salary_from', '-salary_from']:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm(self.request.GET or None)
        
        # Статистика для страницы
        context['total_count'] = self.get_queryset().count()
        context['areas'] = Vacancy.objects.values_list('area', flat=True).distinct()[:10]
        context['experiences'] = Vacancy.objects.values_list('experience', flat=True).distinct()
        
        # Сохраняем параметры поиска
        context['search_params'] = self.request.GET.copy()
        if 'page' in context['search_params']:
            del context['search_params']['page']
        
        return context


class VacancyDetailView(DetailView):
    """Детальная страница вакансии"""
    model = Vacancy
    template_name = 'vacancies/vacancy_detail.html'
    context_object_name = 'vacancy'
    
    def get_object(self, queryset=None):
        # Ищем по hh_id или по id
        hh_id = self.kwargs.get('hh_id')
        if hh_id:
            return get_object_or_404(Vacancy, hh_id=hh_id)
        return get_object_or_404(Vacancy, pk=self.kwargs.get('pk'))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Похожие вакансии
        vacancy = self.object
        similar_vacancies = Vacancy.objects.filter(
            Q(name__icontains=vacancy.name.split()[0]) |
            Q(employer_name=vacancy.employer_name)
        ).exclude(id=vacancy.id)[:4]
        
        context['similar_vacancies'] = similar_vacancies
        context['skills_list'] = [s.strip() for s in vacancy.key_skills.split(',') if s.strip()]
        
        # Форматирование описания
        if vacancy.description:
            # Простая очистка HTML тегов
            import re
            clean_text = re.sub('<[^<]+?>', '', vacancy.description)
            context['clean_description'] = clean_text[:2000] + '...' if len(clean_text) > 2000 else clean_text
        
        return context


class SearchView(TemplateView):
    """Страница поиска вакансий"""
    template_name = 'vacancies/search.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm(self.request.GET or None)
        
        # Получаем популярные фильтры
        api_service = HHApiService()
        context['areas'] = api_service.get_areas()
        context['experiences'] = api_service.get_experiences()
        context['employments'] = api_service.get_employments()
        
        # Если есть поисковый запрос, сразу показываем результаты
        if self.request.GET.get('q'):
            return redirect('vacancy_list?' + self.request.GET.urlencode())
        
        return context
    
    def post(self, request, *args, **kwargs):
        form = SearchForm(request.POST)
        if form.is_valid():
            # Сохраняем поисковый запрос
            search_data = form.cleaned_data
            SearchQuery.objects.create(
                query=search_data.get('query', ''),
                area=search_data.get('area', ''),
                experience=search_data.get('experience', ''),
                employment=search_data.get('employment', ''),
                results_count=0
            )
            
            # Формируем URL для редиректа
            params = []
            for key, value in search_data.items():
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
        context['recent_imports'] = SearchQuery.objects.all().order_by('-search_date')[:10]
        return context
    
    def post(self, request, *args, **kwargs):
        form = ImportForm(request.POST)
        
        if form.is_valid():
            search_query = form.cleaned_data['search_query']
            count = min(form.cleaned_data['count'], 100)  # Ограничиваем 100
            
            # Подготавливаем параметры поиска
            search_params = {
                'text': search_query,
                'per_page': min(count, 50),
                'area': '113',  # Вся Россия
                'order_by': 'relevance'
            }
            
            # Импортируем вакансии
            api_service = HHApiService()
            result = api_service.process_and_save_vacancies(search_params)
            
            if result['success']:
                messages.success(
                    request,
                    f"✅ Успешно импортировано {result['count']} вакансий по запросу '{search_query}'"
                )
                
                # Показываем предупреждения, если есть
                if result.get('errors'):
                    for error in result['errors'][:3]:  # Показываем только 3 ошибки
                        messages.warning(request, f"⚠️ {error}")
                        
            else:
                messages.error(request, f"❌ Ошибка импорта: {result.get('message', 'Неизвестная ошибка')}")
            
            return redirect('import_vacancies')
        
        return self.render_to_response({'import_form': form})


class StatisticsView(TemplateView):
    """Статистика по вакансиям"""
    template_name = 'vacancies/statistics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Основная статистика
        total_vacancies = Vacancy.objects.count()
        total_employers = Vacancy.objects.values('employer_name').distinct().count()
        
        # Статистика по зарплате
        salary_stats = Vacancy.objects.aggregate(
            avg_salary_from=Avg('salary_from'),
            avg_salary_to=Avg('salary_to'),
            max_salary=Max('salary_to'),
            min_salary=Min('salary_from')
        )
        
        # Статистика по опыту
        experience_stats = Vacancy.objects.values('experience').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Статистика по регионам
        area_stats = Vacancy.objects.values('area').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Топ работодателей
        top_employers = Vacancy.objects.values('employer_name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Популярные навыки
        all_skills = []
        vacancies = Vacancy.objects.exclude(key_skills='')
        for vacancy in vacancies:
            skills = [s.strip() for s in vacancy.key_skills.split(',') if s.strip()]
            all_skills.extend(skills)
        
        from collections import Counter
        popular_skills = Counter(all_skills).most_common(15)
        
        # Вакансии по дням (последние 30 дней)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        vacancies_by_day = []
        for i in range(30):
            day = thirty_days_ago + timedelta(days=i)
            count = Vacancy.objects.filter(
                published_at__date=day.date()
            ).count()
            vacancies_by_day.append({
                'date': day.strftime('%d.%m'),
                'count': count
            })
        
        context.update({
            'total_vacancies': total_vacancies,
            'total_employers': total_employers,
            'salary_stats': salary_stats,
            'experience_stats': experience_stats,
            'area_stats': area_stats,
            'top_employers': top_employers,
            'popular_skills': popular_skills,
            'vacancies_by_day': vacancies_by_day,
        })
        
        return context


class CompareVacanciesView(TemplateView):
    """Сравнение вакансий"""
    template_name = 'vacancies/compare.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем ID вакансий для сравнения
        vacancy_ids = self.request.GET.getlist('vacancy_id')
        vacancies = Vacancy.objects.filter(id__in=vacancy_ids[:4])  # Ограничиваем 4
        
        context['vacancies'] = vacancies
        return context


class EmployerDetailView(DetailView):
    """Страница работодателя"""
    template_name = 'vacancies/employer_detail.html'
    context_object_name = 'employer'
    
    def get_object(self, queryset=None):
        employer_name = self.kwargs.get('employer_name')
        vacancies = Vacancy.objects.filter(employer_name=employer_name)
        if not vacancies.exists():
            return None
        
        # Собираем статистику по работодателю
        employer_stats = {
            'name': employer_name,
            'vacancy_count': vacancies.count(),
            'avg_salary_from': int(vacancies.aggregate(avg=Avg('salary_from'))['avg'] or 0),
            'avg_salary_to': int(vacancies.aggregate(avg=Avg('salary_to'))['avg'] or 0),
            'areas': vacancies.values_list('area', flat=True).distinct(),
            'vacancies': vacancies.order_by('-published_at')[:10]
        }
        
        return employer_stats
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.object:
            context['error'] = 'Работодатель не найден'
        return context


# API views
def api_vacancy_search(request):
    """API для быстрого поиска вакансий (AJAX)"""
    if request.method == 'GET':
        query = request.GET.get('q', '').strip()
        if len(query) < 2:
            return JsonResponse({'items': [], 'count': 0})
        
        vacancies = Vacancy.objects.filter(
            Q(name__icontains=query) |
            Q(employer_name__icontains=query)
        ).order_by('-published_at')[:10]
        
        results = []
        for vacancy in vacancies:
            results.append({
                'id': vacancy.id,
                'hh_id': vacancy.hh_id,
                'name': vacancy.name,
                'employer': vacancy.employer_name,
                'area': vacancy.area,
                'salary': vacancy.get_salary_display(),
                'url': f"/vacancies/{vacancy.hh_id}/"
            })
        
        return JsonResponse({'items': results, 'count': len(results)})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def api_get_statistics(request):
    """API для получения статистики"""
    stats = {
        'total_vacancies': Vacancy.objects.count(),
        'total_employers': Vacancy.objects.values('employer_name').distinct().count(),
        'avg_salary': int(Vacancy.objects.filter(
            salary_from__isnull=False
        ).aggregate(avg=Avg('salary_from'))['avg'] or 0),
        'recent_vacancies': Vacancy.objects.count()
    }
    return JsonResponse(stats)


def clear_database(request):
    """Очистка базы данных (только для разработки)"""
    if request.method == 'POST' and request.user.is_superuser:
        Vacancy.objects.all().delete()
        SearchQuery.objects.all().delete()
        messages.success(request, "База данных очищена")
        return redirect('home')
    
    return render(request, 'vacancies/clear_db.html')