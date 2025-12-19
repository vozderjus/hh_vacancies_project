import requests


class HHApiService:
    """Простой сервис для работы с HH API"""
    
    BASE_URL = "https://api.hh.ru/vacancies"
    
    @staticmethod
    def get_vacancies(search_text="", area="1", per_page=10):
        """Получение списка вакансий"""
        params = {
            "text": search_text,
            "area": area,
            "per_page": per_page,
        }
        
        try:
            response = requests.get(HHApiService.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Ошибка при запросе к HH API: {e}")
            return {"items": [], "found": 0}