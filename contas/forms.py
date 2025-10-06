# contas/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Aluno, Personal

# ----------------- utils -----------------
def _digits(s: str) -> str:
    return "".join(ch for ch in (s or "") if ch.isdigit())

def _validate_tel_digits(tel_digits: str):
    # Brasil: 10 (fixo) ou 11 (cel) dígitos com DDD
    if len(tel_digits) not in (10, 11):
        raise ValidationError("Telefone deve ter DDD + número (10 ou 11 dígitos).")

def _validate_cpf_digits(cpf_digits: str):
    if len(cpf_digits) != 11:
        raise ValidationError("CPF deve conter 11 dígitos.")
    # (Opcional) aqui você poderia validar DV do CPF se quiser


# ----------------- Login -----------------
class LoginForm(AuthenticationForm):
    """
    Autentica usando 'username' do Django, mas permite digitar CPF com máscara.
    O username efetivo será o CPF apenas com dígitos (como você salva no User.username).
    """
    username = UsernameField(
        label="CPF",
        widget=forms.TextInput(attrs={"autofocus": True, "placeholder": "000.000.000-00"})
    )

    def clean(self):
        # normaliza CPF antes da autenticação
        data = self.data.copy()
        data["username"] = _digits(data.get("username", ""))
        self.data = data
        return super().clean()


# ----------------- Registro de Aluno -----------------
class RegistroAlunoForm(forms.Form):
    first_name = forms.CharField(label="Nome", max_length=254)
    last_name  = forms.CharField(label="Sobrenome", max_length=254, required=False)
    email      = forms.EmailField(label="E-mail")
    cpf        = forms.CharField(label="CPF", max_length=14, help_text="Ex.: 000.000.000-00")
    tel        = forms.CharField(label="Telefone (com DDD)", max_length=15)
    sex        = forms.ChoiceField(label="Sexo", choices=[("M","Masculino"), ("F","Feminino"), ("O","Outro")])
    date_of_birth = forms.DateField(label="Data de nascimento", widget=forms.DateInput(attrs={"type": "date"}))
    password1  = forms.CharField(label="Senha", widget=forms.PasswordInput)
    password2  = forms.CharField(label="Confirmar senha", widget=forms.PasswordInput)

    def clean_cpf(self):
        raw = self.cleaned_data.get("cpf", "")
        digits = _digits(raw)
        _validate_cpf_digits(digits)

        # Garante unicidade tanto no User.username quanto no Aluno.cpf
        if User.objects.filter(username=digits).exists():
            raise ValidationError("Já existe um usuário com este CPF.")
        if Aluno.objects.filter(cpf__iexact=raw).exists() or Aluno.objects.filter(cpf=digits).exists():
            # protege contra registros antigos com/sem máscara
            raise ValidationError("Já existe um aluno com este CPF.")
        return digits  # retornamos só dígitos; salvaremos assim no User.username

    def clean_tel(self):
        raw = self.cleaned_data.get("tel", "")
        digits = _digits(raw)
        _validate_tel_digits(digits)
        return digits

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1") or ""
        p2 = cleaned.get("password2") or ""
        if p1 != p2:
            raise ValidationError("As senhas não conferem.")
        # valida pelos validadores do Django (complexidade, tamanho etc.)
        validate_password(p1)
        return cleaned

    def save(self):
        first_name = self.cleaned_data["first_name"].strip()
        last_name  = self.cleaned_data.get("last_name", "").strip()
        email      = self.cleaned_data["email"].strip()
        cpf_digits = self.cleaned_data["cpf"]          # já vem só dígitos do clean_cpf
        tel_digits = self.cleaned_data["tel"]          # já vem só dígitos do clean_tel
        sex        = self.cleaned_data["sex"]
        dob        = self.cleaned_data["date_of_birth"]
        password   = self.cleaned_data["password1"]

        # Cria o usuário base (username = CPF dígitos)
        user = User(username=cpf_digits, first_name=first_name, last_name=last_name, email=email)
        user.set_password(password)
        user.save()

        # Cria o perfil Aluno (armazenando cpf com máscara ou não? aqui, salvo só dígitos)
        Aluno.objects.create(
            user=user,
            cpf=cpf_digits,
            first_name=first_name,
            last_name=last_name,
            tel=tel_digits,
            sex=sex,
            email=email,
            date_of_birth=dob,
        )
        return user


# ----------------- Registro de Personal -----------------
class RegistroPersonalForm(forms.Form):
    first_name = forms.CharField(label="Nome", max_length=254)
    last_name  = forms.CharField(label="Sobrenome", max_length=254, required=False)
    email      = forms.EmailField(label="E-mail")
    cpf        = forms.CharField(label="CPF", max_length=14, help_text="Ex.: 000.000.000-00")
    tel        = forms.CharField(label="Telefone (com DDD)", max_length=15)
    sex        = forms.ChoiceField(label="Sexo", choices=[("M","Masculino"), ("F","Feminino"), ("O","Outro")])
    date_of_birth = forms.DateField(label="Data de nascimento", widget=forms.DateInput(attrs={"type": "date"}))
    cref       = forms.CharField(label="CREF", max_length=20)
    password1  = forms.CharField(label="Senha", widget=forms.PasswordInput)
    password2  = forms.CharField(label="Confirmar senha", widget=forms.PasswordInput)

    def clean_cpf(self):
        raw = self.cleaned_data.get("cpf", "")
        digits = _digits(raw)
        _validate_cpf_digits(digits)

        if User.objects.filter(username=digits).exists():
            raise ValidationError("Já existe um usuário com este CPF.")
        # protege contra dados antigos com/sem máscara
        if Personal.objects.filter(cpf__iexact=raw).exists() or Personal.objects.filter(cpf=digits).exists():
            raise ValidationError("Já existe um personal com este CPF.")
        return digits

    def clean_tel(self):
        raw = self.cleaned_data.get("tel", "")
        digits = _digits(raw)
        _validate_tel_digits(digits)
        return digits

    def clean_cref(self):
        cref = (self.cleaned_data.get("cref") or "").strip().upper()
        if Personal.objects.filter(cref=cref).exists():
            raise ValidationError("Já existe um personal com este CREF.")
        return cref

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1") or ""
        p2 = cleaned.get("password2") or ""
        if p1 != p2:
            raise ValidationError("As senhas não conferem.")
        validate_password(p1)
        return cleaned

    def save(self):
        first_name = self.cleaned_data["first_name"].strip()
        last_name  = self.cleaned_data.get("last_name", "").strip()
        email      = self.cleaned_data["email"].strip()
        cpf_digits = self.cleaned_data["cpf"]
        tel_digits = self.cleaned_data["tel"]
        sex        = self.cleaned_data["sex"]
        dob        = self.cleaned_data["date_of_birth"]
        cref       = self.cleaned_data["cref"]
        password   = self.cleaned_data["password1"]

        user = User(username=cpf_digits, first_name=first_name, last_name=last_name, email=email)
        user.set_password(password)
        user.save()

        Personal.objects.create(
            user=user,
            cpf=cpf_digits,
            first_name=first_name,
            last_name=last_name,
            tel=tel_digits,
            sex=sex,
            email=email,
            date_of_birth=dob,
            cref=cref,
            ativo=True,
        )
        return user
