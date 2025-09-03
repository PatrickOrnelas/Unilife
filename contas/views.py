from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

from .forms import LoginForm, RegistroAlunoForm


def destino_por_perfil(user):
    if hasattr(user, "admin"):
        return reverse_lazy("home-admin")
    if hasattr(user, "personal"):
        return reverse_lazy("home-personal")
    if hasattr(user, "aluno"):
        return reverse_lazy("home-aluno")
    # fallback (caso futuro sem perfil)
    return reverse_lazy("home")

class CPFLoginView(LoginView):
    template_name = "global/login.html"
    authentication_form = LoginForm

    def get_success_url(self):
        return destino_por_perfil(self.request.user)

@login_required
def home_redirect(request):
    """Caso você queira uma rota /home/ única que redirecione para a home certa."""
    return redirect(destino_por_perfil(request.user))

@login_required
def home_aluno(request):
    return render(request, "global/home_aluno.html")

@login_required
def home_personal(request):
    return render(request, "global/home_personal.html")

@login_required
def home_admin(request):
    return render(request, "global/home_admin.html")


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
