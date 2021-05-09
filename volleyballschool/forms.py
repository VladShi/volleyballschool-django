from django.contrib.auth import get_user_model
from django.forms import CharField, EmailField, RegexField
from django.contrib.auth.forms import UserCreationForm


class RegisterUserForm(UserCreationForm):

    username = RegexField(
        label='Номер телефона: +7',
        help_text='10 цифр номера. Будет использоваться \
                   для входа в личный кабинет',
        regex='^(([0-9]){10})$',  # проверяем что введено 10 цифр
        strip=True,
        error_messages={'invalid': 'Введите номер телефона из 10 цифр без \
                                    пробелов и дефисов. Например, 9167772211'
                        }
    )
    first_name = CharField(label='Имя')
    last_name = CharField(label='Фамилия')
    patronymic = CharField(label='Отчество')
    email = EmailField(label='Адрес электронной почты')

    class Meta:
        model = get_user_model()
        fields = ('username', 'first_name', 'patronymic',
                  'last_name', 'email', 'password1', 'password2')
