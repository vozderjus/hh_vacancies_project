from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Vacancy, SearchQuery


@receiver(post_save, sender=Vacancy)
def vacancy_saved(sender, instance, created, **kwargs):
    """Сигнал при сохранении вакансии"""
    if created:
        print(f"Создана новая вакансия: {instance.name}")
    else:
        print(f"Обновлена вакансия: {instance.name}")


@receiver(post_save, sender=SearchQuery)
def search_query_saved(sender, instance, created, **kwargs):
    """Сигнал при сохранении поискового запроса"""
    if created:
        print(f"Сохранен новый поисковый запрос: {instance.query}")


# Вы можете добавить другие сигналы по необходимости