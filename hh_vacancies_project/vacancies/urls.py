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
    path('compare/', views.CompareVacanciesView.as_view(), name='compare'),
    path('employer/<str:employer_name>/', views.EmployerDetailView.as_view(), name='employer_detail'),
    
    # API endpoints
    path('api/search/', views.api_vacancy_search, name='api_search'),
    path('api/stats/', views.api_get_statistics, name='api_stats'),
    
    # Утилиты (только для разработки)
    path('clear-db/', views.clear_database, name='clear_db'),
]