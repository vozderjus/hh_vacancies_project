import requests
from datetime import datetime
from typing import List, Dict, Optional
from django.db import transaction
from django.conf import settings
from .models import Vacancy


class HHApiService:
    """Сервис для взаимодействия с HH API"""
    
    BASE_URL = "https://api.hh.ru/vacancies"
    
    @staticmethod
    def get_vacancies(
        search_text: str = "",
        area: str = "1",  # 1 - Москва
        experience: Optional[str] = None,
        employment: Optional[str] = None,
        salary_from: Optional[int] = None,
        salary_to: Optional[int] = None,
        order_by: str = "relevance",
        page: int = 0,
        per_page: int = 50
    ) -> Dict:
        """Получение списка вакансий по заданным параметрам"""
        
        params = {
            "text": search_text,
            "area": area,
            "page": page,
            "per_page": per_page,
            "order_by": order_by,
        }
        
        if experience:
            params["experience"] = experience
        if employment:
            params["employment"] = employment
        if salary_from:
            params["salary"] = salary_from
            if salary_to:
                params["salary"] = f"{salary_from}-{salary_to}"
        
        try:
            response = requests.get(HHApiService.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Ошибка при запросе к HH API: {e}")
            return {"items": [], "found": 0, "pages": 0}
    
    @staticmethod
    def get_vacancy_details(vacancy_id: int) -> Optional[Dict]:
        """Получение детальной информации о конкретной вакансии"""
        
        try:
            response = requests.get(f"{HHApiService.BASE_URL}/{vacancy_id}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Ошибка при получении деталей вакансии {vacancy_id}: {e}")
            return None
    
    @staticmethod
    def save_vacancies_from_api(search_params: Dict) -> List[Vacancy]:
        """Сохранение вакансий из API в базу данных"""
        
        vacancies_data = HHApiService.get_vacancies(**search_params)
        saved_vacancies = []
        
        with transaction.atomic():
            for vacancy_data in vacancies_data.get("items", []):
                # Получаем детальную информацию о вакансии
                detailed_data = HHApiService.get_vacancy_details(vacancy_data["id"])
                
                if not detailed_data:
                    continue
                
                # Парсим информацию о зарплате
                salary_data = detailed_data.get("salary")
                salary_from = salary_to = currency = None
                salary_gross = None
                
                if salary_data:
                    salary_from = salary_data.get("from")
                    salary_to = salary_data.get("to")
                    currency = salary_data.get("currency")
                    salary_gross = salary_data.get("gross")
                
                # Парсим ключевые навыки
                key_skills = ", ".join([skill["name"] for skill in detailed_data.get("key_skills", [])])
                
                # Парсим информацию о работодателе
                employer_data = detailed_data.get("employer", {})
                
                # Создаем или обновляем вакансию
                vacancy, created = Vacancy.objects.update_or_create(
                    hh_id=detailed_data["id"],
                    defaults={
                        "name": detailed_data.get("name", ""),
                        "area": detailed_data.get("area", {}).get("name", ""),
                        "salary_from": salary_from,
                        "salary_to": salary_to,
                        "currency": currency,
                        "salary_gross": salary_gross,
                        "employer_name": employer_data.get("name", ""),
                        "employer_url": employer_data.get("alternate_url"),
                        "description": detailed_data.get("description", ""),
                        "key_skills": key_skills,
                        "experience": detailed_data.get("experience", {}).get("name", ""),
                        "employment": detailed_data.get("employment", {}).get("name", ""),
                        "schedule": detailed_data.get("schedule", {}).get("name", ""),
                        "alternate_url": detailed_data.get("alternate_url", ""),
                        "published_at": datetime.fromisoformat(detailed_data.get("published_at", "")),
                        "response_count": detailed_data.get("response_letter_required", False),
                    }
                )
                
                saved_vacancies.append(vacancy)
        
        return saved_vacancies
    
    @staticmethod
    def get_popular_filters() -> Dict:
        """Получение популярных фильтров для поиска"""
        
        return {
            "experience": [
                {"id": "noExperience", "name": "Без опыта"},
                {"id": "between1And3", "name": "От 1 до 3 лет"},
                {"id": "between3And6", "name": "От 3 до 6 лет"},
                {"id": "moreThan6", "name": "Более 6 лет"},
            ],
            "employment": [
                {"id": "full", "name": "Полная занятость"},
                {"id": "part", "name": "Частичная занятость"},
                {"id": "project", "name": "Проектная работа"},
                {"id": "volunteer", "name": "Волонтерство"},
                {"id": "probation", "name": "Стажировка"},
            ],
            "areas": [
                {"id": "1", "name": "Москва"},
                {"id": "2", "name": "Санкт-Петербург"},
                {"id": "3", "name": "Екатеринбург"},
                {"id": "4", "name": "Новосибирск"},
                {"id": "88", "name": "Казань"},
            ]
        }