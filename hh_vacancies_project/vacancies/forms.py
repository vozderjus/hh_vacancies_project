from django import forms


class SearchForm(forms.Form):
    """Расширенная форма поиска вакансий"""
    query = forms.CharField(
        label="Ключевые слова",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Python разработчик, Data Scientist...',
            'autocomplete': 'off'
        })
    )
    
    area = forms.ChoiceField(
        label="Регион",
        choices=[
            ('', 'Все регионы'),
            ('Москва', 'Москва'),
            ('Санкт-Петербург', 'Санкт-Петербург'),
            ('Новосибирск', 'Новосибирск'),
            ('Екатеринбург', 'Екатеринбург'),
            ('Казань', 'Казань'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    experience = forms.ChoiceField(
        label="Опыт работы",
        choices=[
            ('', 'Любой опыт'),
            ('Без опыта', 'Без опыта'),
            ('От 1 до 3 лет', 'От 1 до 3 лет'),
            ('От 3 до 6 лет', 'От 3 до 6 лет'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    employment = forms.ChoiceField(
        label="Тип занятости",
        choices=[
            ('', 'Любая занятость'),
            ('Полная занятость', 'Полная занятость'),
            ('Частичная занятость', 'Частичная занятость'),
            ('Проектная работа', 'Проектная работа'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    salary_from = forms.IntegerField(
        label="Зарплата от (руб.)",
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '50000'
        })
    )
    
    salary_to = forms.IntegerField(
        label="Зарплата до (руб.)",
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '150000'
        })
    )
    
    sort_by = forms.ChoiceField(
        label="Сортировка",
        choices=[
            ('-published_at', 'Сначала новые'),
            ('published_at', 'Сначала старые'),
            ('-salary_from', 'По убыванию зарплаты'),
            ('salary_from', 'По возрастанию зарплаты'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class ImportForm(forms.Form):
    """Форма для импорта вакансий"""
    search_query = forms.CharField(
        label="Поисковый запрос",
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Введите профессию или ключевые слова',
            'autofocus': True
        })
    )
    
    count = forms.IntegerField(
        label="Количество вакансий",
        min_value=1,
        max_value=100,
        initial=30,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'help_text': 'От 1 до 100 вакансий'
        })
    )
    
    area = forms.ChoiceField(
        label="Регион поиска",
        choices=[
            ('113', 'Вся Россия'),
            ('1', 'Москва'),
            ('2', 'Санкт-Петербург'),
            ('3', 'Екатеринбург'),
            ('4', 'Новосибирск'),
        ],
        initial='113',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class QuickSearchForm(forms.Form):
    """Форма быстрого поиска"""
    q = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Быстрый поиск...',
            'aria-label': 'Поиск'
        })
    )