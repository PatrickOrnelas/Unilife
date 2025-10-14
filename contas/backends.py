# contas/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class CPFBackend(ModelBackend):
    """
    Permite login com CPF (armazenado como username no modelo User).
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        cpf_digits = ''.join(ch for ch in username if ch.isdigit())  # remove máscara
        try:
            user = User.objects.get(username=cpf_digits)
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
