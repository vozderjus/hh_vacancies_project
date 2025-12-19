from .models import Vacancy, SearchQuery


def vacancy_context(request):
    """Контекстный процессор для счетчика вакансий"""
    return {
        'vacancy_count': Vacancy.objects.count(),
        'recent_searches': SearchQuery.objects.all().order_by('-search_date')[:5]
    }