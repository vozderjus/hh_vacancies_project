from django.urls import path
from . import views

urlpatterns = [
    # Главная страница
    path('', views.HomeView.as_view(), name='home'),
    
    # Список вакансий
    path('vacancies/', views.VacancyListView.as_view(), name='vacancy_list'),
    
    # Детальная информация о вакансии
    path('vacancies/<int:hh_id>/', views.VacancyDetailView.as_view(), name='vacancy_detail'),
    
    # Поиск вакансий
    path('search/', views.SearchView.as_view(), name='search'),
    
    # Импорт вакансий
    path('import/', views.ImportVacanciesView.as_view(), name='import_vacancies'),
    
    # Статистика
    path('statistics/', views.StatisticsView.as_view(), name='statistics'),
    
    # API для поиска
    path('api/search/', views.api_search, name='api_search'),
]