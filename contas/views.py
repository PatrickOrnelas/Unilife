from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView

from .forms import LoginForm, RegistroAlunoForm


class CPFLoginView(LoginView):
    template_name = "global/login.html"
    authentication_form = LoginForm

    def get_success_url(self):
        # se quiser redirecionar por perfil:
        # u = self.request.user
        # if hasattr(u, "admin"):    return "/home/"
        # if hasattr(u, "personal"): return "/home/"
        # if hasattr(u, "aluno"):    return "/home/"
        return "/home/"


@login_required
def home(request):
    return render(request, 'global/home.html')


def login_view(request):
    """
    Só manter se você realmente usa uma view manual.
    Como já temos CPFLoginView, normalmente não precisa desta.
    """
    from django.contrib.auth.forms import AuthenticationForm
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        auth_login(request, user)
        return redirect('home')
    return render(request, 'global/login.html', {'form': form})


def registrar(request):
    form = RegistroAlunoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()        # cria User + Aluno
        auth_login(request, user) # opcional: já loga
        return redirect('home')
    return render(request, 'global/registrar.html', {'form': form})


def recuperar_senha_view(request):
    # sua página de "esqueci a senha" custom (entrada por e-mail/CPF)
    return render(request, 'global/reset_password.html')
