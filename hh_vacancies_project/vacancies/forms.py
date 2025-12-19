from django import forms


class SearchForm(forms.Form):
    """Простая форма поиска для теста"""
    query = forms.CharField(
        label='Поиск',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Введите ключевые слова...',
            'class': 'form-control'
        })
    )


class ImportForm(forms.Form):
    """Простая форма импорта для теста"""
    search_text = forms.CharField(
        label='Запрос для поиска',
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Python разработчик...',
            'class': 'form-control'
        })
    )