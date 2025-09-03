import re
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Aluno, Personal

# utilitários
def _digits(s: str) -> str:
    return re.sub(r"\D+", "", s or "")

def validate_cpf(cpf: str) -> str:
    cpf = _digits(cpf)
    # validação simples; troque por uma validação oficial se desejar
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        raise ValidationError("CPF inválido.")
    return cpf

def validate_tel(tel: str) -> str:
    tel = _digits(tel)
    if len(tel) not in (10, 11):
        raise ValidationError("Telefone deve ter DDD + número (10 ou 11 dígitos).")
    return tel

def normalize_cref(texto: str) -> str:
    """
    Normaliza o CREF: trim, upper e colapsa espaços.
    Não removo letras/sinais pois CREF pode ter 'G/SP', etc.
    """
    if not texto:
        return ""
    return re.sub(r"\s+", " ", texto.strip().upper())


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
        # garante que o username usado na auth é só dígitos (CPF)
        return _digits(self.cleaned_data.get("username", ""))


class RegistroAlunoForm(forms.Form):
    first_name     = forms.CharField(max_length=254, label="Nome", required=True)
    last_name      = forms.CharField(max_length=254, label="Sobrenome", required=False)
    email          = forms.EmailField(label="E-mail", required=True)
    cpf            = forms.CharField(max_length=14, label="CPF", required=True)  # aceita com/sem máscara
    tel            = forms.CharField(max_length=16, label="Telefone (DDD + número)", required=True)
    SEX_CHOICES    = [('M', 'Masculino'), ('F', 'Feminino'), ('O', 'Outro')]
    sex            = forms.ChoiceField(choices=SEX_CHOICES, label='Sexo', required=True)
    date_of_birth  = forms.DateField(label='Data de nascimento',
                                     widget=forms.DateInput(attrs={"type": "date"}), required=True)
    password1      = forms.CharField(label="Senha", widget=forms.PasswordInput)
    password2      = forms.CharField(label="Confirmar senha", widget=forms.PasswordInput)

    # --- validações ---
    def clean_cpf(self):
        cpf = validate_cpf(self.cleaned_data.get("cpf"))
        if User.objects.filter(username=cpf).exists():
            raise ValidationError("Já existe um usuário com esse CPF.")
        return cpf

    def clean_tel(self):
        return validate_tel(self.cleaned_data.get("tel"))

    def clean(self):
        data = super().clean()
        p1, p2 = data.get("password1"), data.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "As senhas não conferem.")
        return data

    # --- persistência ---
    def save(self, commit=True):
        first_name    = self.cleaned_data["first_name"].strip()
        last_name     = self.cleaned_data.get("last_name", "").strip()
        email         = self.cleaned_data["email"].strip()
        cpf_digits    = self.cleaned_data["cpf"]      # já só dígitos
        tel_digits    = self.cleaned_data["tel"]      # já só dígitos
        sex           = self.cleaned_data["sex"]
        date_of_birth = self.cleaned_data["date_of_birth"]
        password      = self.cleaned_data["password1"]

        # cria o User com username = CPF
        user = User(username=cpf_digits, first_name=first_name, last_name=last_name, email=email)
        user.set_password(password)

        if commit:
            user.save()
            Aluno.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                tel=tel_digits,
                sex=sex,
                email=email,
                date_of_birth=date_of_birth,
            )
        return user


class RegistroPersonalForm(forms.Form):
    # --- Dados importantes ---
    first_name     = forms.CharField(max_length=254, label="Nome", required=True)  # corrigido label
    last_name      = forms.CharField(max_length=254, label="Sobrenome", required=False)
    email          = forms.EmailField(label="E-mail", required=True)
    cpf            = forms.CharField(max_length=14, label="CPF", required=True)  # aceita com/sem máscara
    cref           = forms.CharField(max_length=20, label="CREF", required=True) # alinhado ao model (20)
    tel            = forms.CharField(max_length=16, label="Telefone (DDD + número)", required=True)
    SEX_CHOICES    = [('M', 'Masculino'), ('F', 'Feminino'), ('O', 'Outro')]
    sex            = forms.ChoiceField(choices=SEX_CHOICES, label="Sexo", required=True)
    date_of_birth  = forms.DateField(label="Data de nascimento",
                                     widget=forms.DateInput(attrs={"type": "date"}), required=True)
    password1      = forms.CharField(label="Senha", widget=forms.PasswordInput)
    password2      = forms.CharField(label="Confirmar senha", widget=forms.PasswordInput)

    # --- Validações ----
    def clean_cpf(self):
        cpf = validate_cpf(self.cleaned_data.get("cpf"))
        if User.objects.filter(username=cpf).exists():
            raise ValidationError("Já existe um usuário com esse CPF.")
        return cpf

    def clean_tel(self):
        return validate_tel(self.cleaned_data.get("tel"))

    def clean_cref(self):
        cref = normalize_cref(self.cleaned_data.get("cref"))
        if len(cref) > 20:
            raise ValidationError("CREF muito longo (máx. 20 caracteres).")
        return cref

    def clean(self):
        data = super().clean()
        p1, p2 = data.get("password1"), data.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "As senhas não conferem.")
        return data

    # --- Persistência ---
    def save(self, commit=True):
        first_name    = self.cleaned_data["first_name"].strip()
        last_name     = self.cleaned_data.get("last_name", "").strip()
        email         = self.cleaned_data["email"].strip()
        cpf_digits    = self.cleaned_data["cpf"]      # já só dígitos
        cref_code     = self.cleaned_data["cref"]     # normalizado (pode ter letras/ /-)
        tel_digits    = self.cleaned_data["tel"]      # já só dígitos
        sex           = self.cleaned_data["sex"]
        date_of_birth = self.cleaned_data["date_of_birth"]
        password      = self.cleaned_data["password1"]

        # cria o User com username = CPF
        user = User(username=cpf_digits, first_name=first_name, last_name=last_name, email=email)
        user.set_password(password)

        if commit:
            user.save()
            Personal.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                tel=tel_digits,
                sex=sex,
                email=email,
                date_of_birth=date_of_birth,
                cref=cref_code,           # <== AGORA salvando o CREF!
                # ativo usa default=True
            )
        return user
