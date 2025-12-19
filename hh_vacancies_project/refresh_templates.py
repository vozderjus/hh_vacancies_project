# Создайте файл refresh_templates.py в корне проекта:
import os
import shutil
import django
from django.conf import settings

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hh_vacancies_project.settings')
django.setup()

# Очистка кэша шаблонов
from django.template.loaders.filesystem import Loader
from django.template.loaders.app_directories import Loader as AppLoader

# Принудительная перезагрузка шаблонов
for loader in [Loader(settings), AppLoader()]:
    loader.reset()

print("Кэш шаблонов очищен")