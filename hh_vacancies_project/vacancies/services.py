import requests
import time
from datetime import datetime
from typing import Dict, List, Optional
from django.db import transaction
from django.utils.timezone import make_aware
from .models import Vacancy, SearchQuery


class HHApiService:
    """Сервис для работы с HH API с реальными запросами"""
    
    BASE_URL = "https://api.hh.ru"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HH-Vacancies-Project/1.0 (contact@example.com)',
            'Accept': 'application/json'
        })
    
    def search_vacancies(self, params: Dict) -> Dict:
        """Поиск вакансий"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/vacancies",
                params=params,
                timeout=15
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при поиске вакансий: {e}")
            return {"items": [], "found": 0, "pages": 0}
    
    def get_vacancy_details(self, vacancy_id: int) -> Optional[Dict]:
        """Получение деталей вакансии"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/vacancies/{vacancy_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении вакансии {vacancy_id}: {e}")
            return None
    
    def get_dictionaries(self):
        """Получение справочников HH"""
        try:
            response = self.session.get(f"{self.BASE_URL}/dictionaries", timeout=10)
            response.raise_for_status()
            return response.json()
        except:
            return {}
    
    def import_vacancies(self, search_params: Dict) -> Dict:
        """Импорт вакансий с сохранением в БД"""
        
        # Подготавливаем параметры
        params = {
            'text': search_params.get('text', ''),
            'area': search_params.get('area', '113'),  # Россия по умолчанию
            'per_page': min(search_params.get('per_page', 20), 100),  # HH ограничивает 100
            'page': search_params.get('page', 0),
            'only_with_salary': search_params.get('only_with_salary', False),
            'order_by': search_params.get('order_by', 'relevance')
        }
        
        # Добавляем дополнительные фильтры
        if search_params.get('experience'):
            params['experience'] = search_params['experience']
        if search_params.get('employment'):
            params['employment'] = search_params['employment']
        if search_params.get('schedule'):
            params['schedule'] = search_params['schedule']
        if search_params.get('salary'):
            params['salary'] = search_params['salary']
        
        print(f"Запрашиваем вакансии с параметрами: {params}")
        
        try:
            # Получаем вакансии
            vacancies_data = self.search_vacancies(params)
            
            if not vacancies_data.get('items'):
                return {
                    'success': False,
                    'message': 'Вакансии не найдены по данному запросу',
                    'count': 0
                }
            
            total_found = vacancies_data.get('found', 0)
            pages = vacancies_data.get('pages', 0)
            
            print(f"Найдено {total_found} вакансий, {pages} страниц")
            
            saved_count = 0
            errors = []
            
            # Ограничиваем количество для обработки
            max_to_process = min(len(vacancies_data['items']), params['per_page'])
            
            for i, vacancy_data in enumerate(vacancies_data['items'][:max_to_process]):
                try:
                    vacancy_id = vacancy_data.get('id')
                    if not vacancy_id:
                        continue
                    
                    # Небольшая задержка между запросами
                    if i > 0 and i % 5 == 0:
                        time.sleep(0.5)
                    
                    # Получаем детали
                    details = self.get_vacancy_details(vacancy_id)
                    if not details:
                        continue
                    
                    # Обрабатываем данные
                    processed_data = self._process_vacancy_data(details)
                    
                    # Сохраняем в БД
                    vacancy, created = self._save_vacancy(processed_data)
                    
                    if created:
                        saved_count += 1
                    
                    print(f"Обработано: {i+1}/{max_to_process} - {vacancy.name}")
                    
                except Exception as e:
                    error_msg = f"Ошибка при обработке вакансии {vacancy_data.get('id')}: {str(e)}"
                    print(error_msg)
                    errors.append(error_msg)
                    continue
            
            # Сохраняем запрос в историю
            if saved_count > 0:
                SearchQuery.objects.create(
                    query=params['text'],
                    area=params.get('area', ''),
                    experience=params.get('experience', ''),
                    employment=params.get('employment', ''),
                    results_count=saved_count
                )
            
            result = {
                'success': True,
                'count': saved_count,
                'total_found': total_found,
                'pages': pages,
                'errors': errors[:3] if errors else []
            }
            
            print(f"Импорт завершен: {result}")
            return result
            
        except Exception as e:
            error_msg = f"Ошибка при импорте: {str(e)}"
            print(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'count': 0
            }
    
    def _process_vacancy_data(self, data: Dict) -> Dict:
        """Обработка данных вакансии"""
        
        # Зарплата
        salary = data.get('salary')
        salary_from = salary.get('from') if salary else None
        salary_to = salary.get('to') if salary else None
        currency = salary.get('currency', 'RUR') if salary else None
        salary_gross = salary.get('gross') if salary else None
        
        # Дата публикации
        published_at_str = data.get('published_at', '').replace('Z', '+00:00')
        try:
            published_at = make_aware(datetime.fromisoformat(published_at_str))
        except:
            published_at = make_aware(datetime.now())
        
        # Навыки
        key_skills = data.get('key_skills', [])
        skills_text = ', '.join([skill['name'] for skill in key_skills])
        
        # Обработка HTML описания (упрощенная)
        description = data.get('description', '')
        # Можно добавить очистку HTML тегов здесь
        
        return {
            'hh_id': data['id'],
            'name': data.get('name', '')[:200],
            'area': data.get('area', {}).get('name', 'Не указано')[:100],
            'salary_from': salary_from,
            'salary_to': salary_to,
            'currency': currency,
            'salary_gross': salary_gross,
            'employer_name': data.get('employer', {}).get('name', '')[:200],
            'employer_url': data.get('employer', {}).get('alternate_url', ''),
            'description': description[:10000],
            'key_skills': skills_text[:500],
            'experience': data.get('experience', {}).get('name', 'Не указано')[:100],
            'employment': data.get('employment', {}).get('name', 'Не указано')[:100],
            'schedule': data.get('schedule', {}).get('name', 'Не указано')[:100],
            'alternate_url': data.get('alternate_url', ''),
            'published_at': published_at,
        }
    
    def _save_vacancy(self, data: Dict):
        """Сохранение вакансии в БД"""
        with transaction.atomic():
            vacancy, created = Vacancy.objects.update_or_create(
                hh_id=data['hh_id'],
                defaults=data
            )
        return vacancy, created
    
    def get_areas(self) -> List[Dict]:
        """Получение списка регионов"""
        try:
            response = self.session.get(f"{self.BASE_URL}/areas", timeout=10)
            response.raise_for_status()
            areas = response.json()
            
            # Фильтруем только Россию и популярные города
            russia = next((area for area in areas if area['name'] == 'Россия'), None)
            if russia:
                popular_cities = []
                for region in russia.get('areas', []):
                    if region['name'] in ['Москва', 'Санкт-Петербург']:
                        popular_cities.append({'id': region['id'], 'name': region['name']})
                    for city in region.get('areas', []):
                        if city['name'] in ['Екатеринбург', 'Новосибирск', 'Казань', 'Нижний Новгород']:
                            popular_cities.append({'id': city['id'], 'name': city['name']})
                
                return [
                    {'id': '113', 'name': 'Вся Россия'},
                    *popular_cities
                ]
        except:
            pass
        
        # Возвращаем статичный список если API не доступно
        return [
            {'id': '113', 'name': 'Вся Россия'},
            {'id': '1', 'name': 'Москва'},
            {'id': '2', 'name': 'Санкт-Петербург'},
            {'id': '3', 'name': 'Екатеринбург'},
            {'id': '4', 'name': 'Новосибирск'},
            {'id': '88', 'name': 'Казань'},
            {'id': '66', 'name': 'Нижний Новгород'},
        ]
    
    def quick_search(self, query: str, limit: int = 10) -> List[Dict]:
        """Быстрый поиск вакансий (для автодополнения)"""
        params = {
            'text': query,
            'per_page': limit,
            'order_by': 'relevance'
        }
        
        try:
            data = self.search_vacancies(params)
            results = []
            
            for item in data.get('items', [])[:limit]:
                salary = item.get('salary', {})
                results.append({
                    'id': item['id'],
                    'name': item.get('name', ''),
                    'employer': item.get('employer', {}).get('name', ''),
                    'area': item.get('area', {}).get('name', ''),
                    'salary_from': salary.get('from'),
                    'salary_to': salary.get('to'),
                    'currency': salary.get('currency'),
                    'alternate_url': item.get('alternate_url', ''),
                })
            
            return results
        except:
            return []
    
    def test_connection(self) -> bool:
        """Тестирование подключения к API"""
        try:
            response = self.session.get(f"{self.BASE_URL}/vacancies", params={'per_page': 1}, timeout=5)
            return response.status_code == 200
        except:
            return False