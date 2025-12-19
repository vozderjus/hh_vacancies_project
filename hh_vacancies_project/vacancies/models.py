from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Vacancy(models.Model):
    """Модель для хранения информации о вакансиях с HH API"""
    
    # Основная информация
    hh_id = models.IntegerField(unique=True, verbose_name="ID вакансии на HH")
    name = models.CharField(max_length=255, verbose_name="Название вакансии")
    area = models.CharField(max_length=100, verbose_name="Регион")
    
    # Информация о зарплате
    salary_from = models.IntegerField(null=True, blank=True, verbose_name="Зарплата от")
    salary_to = models.IntegerField(null=True, blank=True, verbose_name="Зарплата до")
    currency = models.CharField(max_length=10, null=True, blank=True, verbose_name="Валюта")
    salary_gross = models.BooleanField(null=True, verbose_name="Зарплата до вычета налогов")
    
    # Информация о работодателе
    employer_name = models.CharField(max_length=255, verbose_name="Название работодателя")
    employer_url = models.URLField(null=True, blank=True, verbose_name="Ссылка на работодателя")
    
    # Описание
    description = models.TextField(verbose_name="Описание вакансии")
    key_skills = models.TextField(verbose_name="Ключевые навыки")
    
    # Детали вакансии
    experience = models.CharField(max_length=100, verbose_name="Требуемый опыт")
    employment = models.CharField(max_length=100, verbose_name="Тип занятости")
    schedule = models.CharField(max_length=100, verbose_name="График работы")
    
    # Ссылки и даты
    alternate_url = models.URLField(verbose_name="Ссылка на вакансию на HH")
    published_at = models.DateTimeField(verbose_name="Дата публикации")
    
    # Статистика
    response_count = models.IntegerField(default=0, verbose_name="Количество откликов")
    
    class Meta:
        verbose_name = "Вакансия"
        verbose_name_plural = "Вакансии"
        ordering = ['-published_at']
    
    def __str__(self):
        return f"{self.name} ({self.employer_name})"
    
    def get_salary_display(self):
        """Форматированное отображение зарплаты"""
        if self.salary_from and self.salary_to:
            return f"{self.salary_from:,} - {self.salary_to:,} {self.currency or ''}"
        elif self.salary_from:
            return f"от {self.salary_from:,} {self.currency or ''}"
        elif self.salary_to:
            return f"до {self.salary_to:,} {self.currency or ''}"
        return "Не указана"


class SearchQuery(models.Model):
    """Модель для сохранения истории поисковых запросов"""
    query = models.CharField(max_length=255, verbose_name="Поисковый запрос")
    area = models.CharField(max_length=100, blank=True, null=True, verbose_name="Регион")
    experience = models.CharField(max_length=50, blank=True, null=True, verbose_name="Опыт")
    employment = models.CharField(max_length=50, blank=True, null=True, verbose_name="Занятость")
    search_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата поиска")
    results_count = models.IntegerField(default=0, verbose_name="Количество результатов")
    
    class Meta:
        verbose_name = "Поисковый запрос"
        verbose_name_plural = "История поисковых запросов"
        ordering = ['-search_date']
    
    def __str__(self):
        return f"{self.query} - {self.search_date.strftime('%Y-%m-%d %H:%M')}"