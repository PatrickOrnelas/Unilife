# contas/views.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.views.decorators.http import require_http_methods, require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .forms import LoginForm, RegistroAlunoForm, RegistroPersonalForm
from .models import Personal


def destino_por_perfil(user):
    if hasattr(user, "admin"):
        return reverse_lazy("home-admin")
    if hasattr(user, "personal"):
        return reverse_lazy("home-personal")
    if hasattr(user, "aluno"):
        return reverse_lazy("home-aluno")
    return reverse_lazy("home")


class CPFLoginView(LoginView):
    template_name = "global/login.html"
    authentication_form = LoginForm

    def get_success_url(self):
        return destino_por_perfil(self.request.user)


@login_required
def home_redirect(request):
    return redirect(destino_por_perfil(request.user))


@login_required
def home_aluno(request):
    return render(request, "global/home_aluno.html")


@login_required
def home_personal(request):
    return render(request, "global/home_personal.html")


@login_required
def home_admin(request):
    """
    Renderiza o painel admin. Se quiser já abrir a aba 'perfil',
    use /admin/home/#perfil no navegador.
    """
    return render(request, "global/home_admin.html")


def login_view(request):
    # Mantido apenas se você ainda quiser uma view manual.
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
        user = form.save()
        auth_login(request, user)
        return redirect('home')
    return render(request, 'global/registrar.html', {'form': form})


def recuperar_senha_view(request):
    return render(request, 'global/reset_password.html')


def is_admin(user):
    return hasattr(user, "admin")


# --------- Personais (views normais, sem API) ---------

@login_required
@user_passes_test(is_admin)
def cadastrar_personal(request):
    form = RegistroPersonalForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Personal cadastrado com sucesso!")
        # volta para a mesma tela abrindo a aba de cadastro
        resp = redirect('home-admin')
        resp['Location'] += "#cadastrar-personal"
        return resp
    # Mostra a mesma home com a aba "Cadastrar Personal" selecionada
    return render(request, 'global/home_admin.html', {
        'form': form,
        'view': 'cadastrar-personal'
    })


@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def gerenciar_personal(request):
    """
    Lista/filtra em GET e aplica ações em massa via POST (ativar, desativar, deletar).
    """
    # --- Ações em massa (POST) ---
    if request.method == "POST":
        action = request.POST.get("action")
        ids = request.POST.getlist("ids")
        qs = Personal.objects.filter(pk__in=ids)

        if not ids:
            messages.error(request, "Selecione pelo menos um registro.")
            return redirect("gerenciar-personal")

        if action == "activate":
            qs.update(ativo=True)
            messages.success(request, f"{qs.count()} personal(is) ativado(s).")
        elif action == "deactivate":
            qs.update(ativo=False)
            messages.success(request, f"{qs.count()} personal(is) desativado(s).")
        elif action == "delete":
            n = qs.count()
            qs.delete()
            messages.success(request, f"{n} personal(is) removido(s).")
        else:
            messages.error(request, "Ação inválida.")

        return redirect(request.get_full_path())

    # --- Listagem (GET) ---
    q      = request.GET.get("q", "").strip()
    sex    = request.GET.get("sex", "")        # 'M' | 'F' | 'O' | ''
    status = request.GET.get("status", "")     # 'active' | 'inactive' | ''

    people = Personal.objects.all().order_by("-id")

    if q:
        people = people.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)  |
            Q(email__icontains=q)      |
            Q(cpf__icontains=q)        |
            Q(cref__icontains=q)
        )
    if sex in ("M", "F", "O"):
        people = people.filter(sex=sex)
    if status == "active":
        people = people.filter(ativo=True)
    elif status == "inactive":
        people = people.filter(ativo=False)

    paginator = Paginator(people, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Renderize sua própria página de “Gerenciar Personal” caso tenha um template dedicado.
    # Se preferir usar a mesma home com a aba “gerenciar-personal”, também funciona.
    return render(request, "global/gerenciar_personal.html", {
        "page_obj": page_obj,
        "q": q, "sex": sex, "status": status
    })


@login_required
@user_passes_test(is_admin)
@require_POST
def personal_toggle(request, pk):
    p = get_object_or_404(Personal, pk=pk)
    p.ativo = not p.ativo
    p.save(update_fields=["ativo"])
    messages.success(request, f'{p.first_name} {"ativado" if p.ativo else "desativado"}.')
    return redirect(request.META.get("HTTP_REFERER", "gerenciar-personal"))


@login_required
@user_passes_test(is_admin)
@require_POST
def personal_delete(request, pk):
    p = get_object_or_404(Personal, pk=pk)
    p.delete()
    messages.success(request, "Personal removido.")
    return redirect(request.META.get("HTTP_REFERER", "gerenciar-personal"))


# --------- Alterar senha no perfil (funcionando) ---------

@login_required
@require_POST
def change_password(request):
    """
    Troca a senha do usuário autenticado e mantém a sessão.
    Essa view espera campos 'password1' e 'password2'.
    """
    p1 = (request.POST.get("password1") or "").strip()
    p2 = (request.POST.get("password2") or "").strip()

    if not p1 or not p2:
        messages.error(request, "Preencha os dois campos de senha.")
        return _redir_perfil(request)

    if p1 != p2:
        messages.error(request, "As senhas não conferem.")
        return _redir_perfil(request)

    try:
        validate_password(p1, user=request.user)
    except ValidationError as e:
        for msg in e.messages:
            messages.error(request, msg)
        return _redir_perfil(request)

    user = request.user
    user.set_password(p1)
    user.save(update_fields=["password"])
    update_session_auth_hash(request, user)  # evita logout

    messages.success(request, "Senha atualizada com sucesso!")
    return _redir_perfil(request)


def _redir_perfil(request):
    """
    Sempre volta para a home do admin com a aba de Perfil aberta.
    Se o usuário não for admin, volte para a home adequada.
    """
    if hasattr(request.user, "admin"):
        resp = redirect("home-admin")
        resp["Location"] += "#perfil"
        return resp
    # fallback: volta para sua home padrão
    return redirect("home")
