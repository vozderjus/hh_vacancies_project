import requests
from datetime import datetime
from typing import Dict, List, Optional
from django.db import transaction
from django.utils.timezone import make_aware
from .models import Vacancy, SearchQuery


class HHApiService:
    """Сервис для реальной работы с HH API"""
    
    BASE_URL = "https://api.hh.ru/vacancies"
    
    @staticmethod
    def fetch_vacancies(params: Dict) -> Dict:
        """Получение вакансий с HH API"""
        try:
            response = requests.get(
                HHApiService.BASE_URL,
                params=params,
                headers={'User-Agent': 'HH-Vacancies-App/1.0'},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Ошибка API: {e}")
            return {"items": [], "found": 0, "pages": 0}
    
    @staticmethod
    def fetch_vacancy_details(vacancy_id: int) -> Optional[Dict]:
        """Получение детальной информации о вакансии"""
        try:
            response = requests.get(
                f"{HHApiService.BASE_URL}/{vacancy_id}",
                headers={'User-Agent': 'HH-Vacancies-App/1.0'},
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Ошибка получения деталей: {e}")
            return None
    
    @staticmethod
    def process_and_save_vacancies(search_params: Dict) -> Dict:
        """Обработка и сохранение вакансий"""
        try:
            # Получаем вакансии
            vacancies_data = HHApiService.fetch_vacancies(search_params)
            
            if not vacancies_data.get('items'):
                return {'success': False, 'message': 'Вакансии не найдены', 'count': 0}
            
            saved_count = 0
            errors = []
            
            # Ограничиваем количество для обработки
            max_vacancies = min(len(vacancies_data['items']), 50)
            
            for i, vacancy_data in enumerate(vacancies_data['items'][:max_vacancies]):
                try:
                    # Получаем детали
                    details = HHApiService.fetch_vacancy_details(vacancy_data['id'])
                    if not details:
                        continue
                    
                    # Обрабатываем зарплату
                    salary = details.get('salary', {})
                    salary_from = salary.get('from')
                    salary_to = salary.get('to')
                    currency = salary.get('currency', 'RUR')
                    
                    # Обрабатываем опыт
                    experience = details.get('experience', {}).get('name', 'Не указано')
                    
                    # Обрабатываем занятость
                    employment = details.get('employment', {}).get('name', 'Не указано')
                    
                    # Ключевые навыки
                    key_skills_list = [skill['name'] for skill in details.get('key_skills', [])]
                    key_skills = ', '.join(key_skills_list[:10])  # Ограничиваем 10 навыков
                    
                    # Описание (очищаем HTML теги)
                    description = details.get('description', '')
                    
                    # Парсим дату
                    published_at_str = details.get('published_at', '').replace('Z', '+00:00')
                    try:
                        published_at = make_aware(datetime.fromisoformat(published_at_str))
                    except:
                        published_at = make_aware(datetime.now())
                    
                    # Создаем или обновляем вакансию
                    vacancy, created = Vacancy.objects.update_or_create(
                        hh_id=details['id'],
                        defaults={
                            'name': details.get('name', '')[:250],
                            'area': details.get('area', {}).get('name', 'Не указано')[:100],
                            'salary_from': salary_from,
                            'salary_to': salary_to,
                            'currency': currency,
                            'employer_name': details.get('employer', {}).get('name', '')[:250],
                            'employer_url': details.get('employer', {}).get('alternate_url', ''),
                            'description': description[:5000],
                            'key_skills': key_skills,
                            'experience': experience[:100],
                            'employment': employment[:100],
                            'schedule': details.get('schedule', {}).get('name', '')[:100],
                            'alternate_url': details.get('alternate_url', ''),
                            'published_at': published_at,
                        }
                    )
                    
                    saved_count += 1
                    
                    # Делаем небольшую паузу между запросами
                    if i % 5 == 0:
                        import time
                        time.sleep(0.1)
                    
                except Exception as e:
                    errors.append(f"Вакансия {vacancy_data.get('id', 'Unknown')}: {str(e)[:50]}")
                    continue
            
            # Сохраняем поисковый запрос
            if saved_count > 0:
                SearchQuery.objects.create(
                    query=search_params.get('text', '')[:250],
                    area=search_params.get('area', ''),
                    experience=search_params.get('experience', ''),
                    employment=search_params.get('employment', ''),
                    results_count=saved_count
                )
            
            return {
                'success': True,
                'count': saved_count,
                'total_found': vacancies_data.get('found', 0),
                'errors': errors[:3] if errors else []
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Ошибка обработки: {str(e)}', 'count': 0}
    
    @staticmethod
    def get_areas() -> List[Dict]:
        """Получение списка регионов"""
        return [
            {'id': '113', 'name': 'Россия'},
            {'id': '1', 'name': 'Москва'},
            {'id': '2', 'name': 'Санкт-Петербург'},
            {'id': '3', 'name': 'Екатеринбург'},
            {'id': '4', 'name': 'Новосибирск'},
            {'id': '88', 'name': 'Казань'},
            {'id': '66', 'name': 'Нижний Новгород'},
            {'id': '104', 'name': 'Челябинск'},
        ]
    
    @staticmethod
    def get_experiences() -> List[Dict]:
        """Получение вариантов опыта"""
        return [
            {'id': '', 'name': 'Любой опыт'},
            {'id': 'noExperience', 'name': 'Без опыта'},
            {'id': 'between1And3', 'name': 'От 1 до 3 лет'},
            {'id': 'between3And6', 'name': 'От 3 до 6 лет'},
            {'id': 'moreThan6', 'name': 'Более 6 лет'},
        ]
    
    @staticmethod
    def get_employments() -> List[Dict]:
        """Получение типов занятости"""
        return [
            {'id': '', 'name': 'Любая занятость'},
            {'id': 'full', 'name': 'Полная занятость'},
            {'id': 'part', 'name': 'Частичная занятость'},
            {'id': 'project', 'name': 'Проектная работа'},
            {'id': 'volunteer', 'name': 'Волонтерство'},
            {'id': 'probation', 'name': 'Стажировка'},
        ]
    
    @staticmethod
    def search_vacancies_api(params: Dict) -> Dict:
        """Поиск вакансий через API"""
        return HHApiService.fetch_vacancies(params)
    
    @staticmethod
    def get_popular_skills_from_db(limit: int = 10) -> List[Dict]:
        """Получение популярных навыков из базы"""
        from collections import Counter
        
        all_skills = []
        vacancies = Vacancy.objects.exclude(key_skills='').only('key_skills')
        
        for vacancy in vacancies:
            skills = [s.strip() for s in vacancy.key_skills.split(',') if s.strip()]
            all_skills.extend(skills)
        
        skill_counter = Counter(all_skills)
        result = []
        
        for skill, count in skill_counter.most_common(limit):
            result.append({
                'name': skill,
                'count': count,
                'percentage': round(count / len(vacancies) * 100, 1) if vacancies else 0
            })
        
        return result