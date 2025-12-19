from django import forms


class SearchForm(forms.Form):
    """Форма для поиска вакансий"""
    
    query = forms.CharField(
        label="Ключевые слова",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: Python разработчик'
        })
    )
    
    area = forms.ChoiceField(
        label="Регион",
        choices=[
            ('1', 'Москва'),
            ('2', 'Санкт-Петербург'),
            ('3', 'Екатеринбург'),
            ('4', 'Новосибирск'),
            ('88', 'Казань'),
            ('113', 'Россия'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    experience = forms.ChoiceField(
        label="Опыт работы",
        choices=[
            ('', 'Любой'),
            ('noExperience', 'Без опыта'),
            ('between1And3', 'От 1 до 3 лет'),
            ('between3And6', 'От 3 до 6 лет'),
            ('moreThan6', 'Более 6 лет'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    employment = forms.ChoiceField(
        label="Тип занятости",
        choices=[
            ('', 'Любой'),
            ('full', 'Полная занятость'),
            ('part', 'Частичная занятость'),
            ('project', 'Проектная работа'),
            ('volunteer', 'Волонтерство'),
            ('probation', 'Стажировка'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    salary_from = forms.IntegerField(
        label="Зарплата от",
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: 50000'
        })
    )
    
    salary_to = forms.IntegerField(
        label="Зарплата до",
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: 150000'
        })
    )


class ImportForm(forms.Form):
    """Форма для импорта вакансий с HH API"""
    
    search_query = forms.CharField(
        label="Поисковый запрос",
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ключевые слова для поиска'
        })
    )
    
    count = forms.IntegerField(
        label="Количество вакансий",
        min_value=1,
        max_value=100,
        initial=20,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )