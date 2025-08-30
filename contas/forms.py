import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Cadastros
from django import forms
from django.contrib.auth.forms import AuthenticationForm

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="CPF",
        widget=forms.TextInput(attrs={"placeholder": "000.000.000-00", "autocomplete": "username"})
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••", "autocomplete": "current-password"})
    )

    def clean_username(self):
        username = self.cleaned_data.get("username", "")
        return ''.join(filter(str.isdigit, username))  # só dígitos



def _digits(s: str) -> str:
    return re.sub(r"\D+", "", s or "")

def validate_cpf(cpf: str) -> str:
    cpf = _digits(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        raise ValidationError("CPF inválido.")
    return cpf

def validate_tel(tel: str) -> str:
    tel = _digits(tel)
    if len(tel) not in (10, 11):
        raise ValidationError("Telefone deve ter DDD + número (10 ou 11 dígitos).")
    return tel

class RegistroForm(UserCreationForm):
    first_name    = forms.CharField(max_length=254, label="Nome", required=True)
    last_name     = forms.CharField(max_length=254, label="Sobrenome", required=False)
    email         = forms.EmailField(label="E-mail", required=True)
    cpf           = forms.CharField(max_length=14, label="CPF", required=True)   # aceita com/sem máscara
    tel           = forms.CharField(max_length=15, label="Telefone (DDD + número)", required=True)
    sex           = forms.ChoiceField(choices=Cadastros.SEX_CHOICES, label='Sexo', required=True)
    date_of_birth = forms.DateField(label='Data de nascimento',
                                    widget=forms.DateInput(attrs={"type": "date"}), required=True)
    restrictions  = forms.CharField(
        label='Restrições', required=False,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Ex.: dor lombar, hipertensão..."})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("password1", "password2")

    def clean_cpf(self):
        cpf = validate_cpf(self.cleaned_data.get("cpf"))
        if User.objects.filter(username=cpf).exists():
            raise ValidationError("Já existe um usuário com esse CPF.")
        if Cadastros.objects.filter(cpf=cpf).exists():
            raise ValidationError("Já existe um cadastro com esse CPF.")
        return cpf

    def clean_tel(self):
        return validate_tel(self.cleaned_data.get("tel"))

    def save(self, commit=True):
        user = super().save(commit=False)

        first_name    = self.cleaned_data["first_name"].strip()
        last_name     = self.cleaned_data.get("last_name", "").strip()
        email         = self.cleaned_data["email"].strip()
        cpf           = _digits(self.cleaned_data["cpf"])
        tel           = _digits(self.cleaned_data["tel"])
        sex           = self.cleaned_data["sex"]
        date_of_birth = self.cleaned_data["date_of_birth"]
        restrictions  = self.cleaned_data.get("restrictions", "")

        # username = CPF (apenas dígitos)
        user.username   = cpf
        user.first_name = first_name
        user.last_name  = last_name
        user.email      = email

        if commit:
            user.save()
            Cadastros.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                cpf=cpf,
                tel=tel,
                sex=sex,
                date_of_birth=date_of_birth,
                restrictions=restrictions,
            )
        return user
