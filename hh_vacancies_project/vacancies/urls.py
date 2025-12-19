from django.urls import path
from . import views

urlpatterns = [
    # Основные маршруты
    path('', views.HomeView.as_view(), name='home'),
    path('vacancies/', views.VacancyListView.as_view(), name='vacancy_list'),
    path('vacancies/<int:hh_id>/', views.VacancyDetailView.as_view(), name='vacancy_detail'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('import/', views.ImportVacanciesView.as_view(), name='import_vacancies'),
    path('statistics/', views.StatisticsView.as_view(), name='statistics'),
    
    # API endpoints
    path('api/search/', views.api_vacancy_search, name='api_search'),
    path('api/stats/', views.api_get_statistics, name='api_stats'),
    
    # Утилиты
    path('clear-db/', views.clear_database, name='clear_db'),
    path('test-api/', views.test_api_view, name='test_api'),
]