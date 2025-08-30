from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegistroForm
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView
from .forms import LoginForm

class CPFLoginView(LoginView):
    template_name = "global/login.html"
    authentication_form = LoginForm

    def get_success_url(self):
        return "/home/"   # ou use reverse_lazy('home')


@login_required
def home(request):
    return render(request, 'global/home.html')

def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        auth_login(request, user)
        return redirect('home')
    return render(request, 'global/login.html', {'form': form})

def registrar(request):
    form = RegistroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()           # <-- AQUI salva no banco (User + Alunos)
        auth_login(request, user)    # opcional: já loga o usuário
        return redirect('home')      # depois redireciona
    return render(request, 'global/registrar.html', {'form': form})

def recuperar_senha_view(request):
    return render(request, 'global/reset_password.html')
