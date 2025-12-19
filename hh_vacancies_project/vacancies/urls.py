from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('vacancies/', views.VacancyListView.as_view(), name='vacancy_list'),
    path('vacancies/<int:hh_id>/', views.VacancyDetailView.as_view(), name='vacancy_detail'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('import/', views.ImportVacanciesView.as_view(), name='import_vacancies'),
    path('statistics/', views.StatisticsView.as_view(), name='statistics'),
    # path('api/search/', views.api_search, name='api_search'),  # Пока отключим
]