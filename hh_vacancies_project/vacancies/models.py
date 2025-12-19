from django.db import models


class Vacancy(models.Model):
    """Минимальная модель вакансии"""
    name = models.CharField(max_length=255, verbose_name="Название")
    employer_name = models.CharField(max_length=255, verbose_name="Работодатель")
    area = models.CharField(max_length=100, verbose_name="Регион", default="Москва")
    salary_from = models.IntegerField(null=True, blank=True, verbose_name="Зарплата от")
    salary_to = models.IntegerField(null=True, blank=True, verbose_name="Зарплата до")
    published_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Вакансия"
        verbose_name_plural = "Вакансии"


class SearchQuery(models.Model):
    """Модель для истории поиска"""
    query = models.CharField(max_length=255, verbose_name="Запрос")
    search_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата поиска")
    
    def __str__(self):
        return self.query