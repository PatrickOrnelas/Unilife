from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from .forms import LoginForm, RegistroAlunoForm, RegistroPersonalForm
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
import json
from .models import Personal
from django.contrib import messages


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
    return render(request, "global/home_admin.html")


def login_view(request):
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


@login_required
@user_passes_test(is_admin)
def cadastrar_personal(request):
    form = RegistroPersonalForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Personal cadastrado com sucesso!")
        return redirect('home-admin')
    return render(request, 'global/home_admin.html', {'form': form, 'view': 'cadastrar-personal'})


# ========= GERENCIAR PERSONAL (API) =========

@login_required
@user_passes_test(is_admin)
@require_GET
def api_personals(request):
    q         = request.GET.get('q', '').strip()
    sex       = request.GET.get('sex')        # 'M' | 'F' | 'O' | ''
    status    = request.GET.get('status')     # 'active' | 'inactive' | ''
    ordering  = request.GET.get('ordering', '-created_at')
    page      = int(request.GET.get('page', 1))
    page_size = min(int(request.GET.get('page_size', 10)), 100)

    qs = Personal.objects.all()

    if q:
        qs = qs.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)  |
            Q(email__icontains=q)      |
            Q(cpf__icontains=q)        |
            Q(tel__icontains=q)
        )
    if sex in ('M','F','O'):
        qs = qs.filter(sex=sex)
    if status in ('active','inactive'):
        qs = qs.filter(ativo=(status == 'active'))  # <== usa "ativo"

    try:
        qs = qs.order_by(ordering)
    except Exception:
        qs = qs.order_by('-id')

    paginator = Paginator(qs, page_size)
    page_obj  = paginator.get_page(page)

    def row(p):
        return {
            'id': p.id,
            'first_name': getattr(p, 'first_name', '') or '',
            'last_name':  getattr(p, 'last_name', '')  or '',
            'cpf':        getattr(p, 'cpf', '')        or '',
            'cref':       getattr(p, 'cref', '')       or '',
            'tel':        getattr(p, 'tel', '')        or '',
            'sex':        getattr(p, 'sex', '')        or '',
            'email':      getattr(p, 'email', '')      or '',
            'is_active':  getattr(p, 'ativo', True),        # mantém chave da UI
            'created_at': getattr(p, 'created_at', None).isoformat() if getattr(p, 'created_at', None) else '',
        }

    return JsonResponse({
        'results': [row(p) for p in page_obj.object_list],
        'page': page_obj.number,
        'num_pages': paginator.num_pages,
        'count': paginator.count,
    })


@login_required
@user_passes_test(is_admin)
@require_POST
def api_personals_bulk(request):
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return HttpResponseBadRequest('JSON inválido.')

    action = payload.get('action')
    ids    = payload.get('ids') or []
    qs     = Personal.objects.filter(id__in=ids)

    if action == 'activate':
        qs.update(ativo=True)
    elif action == 'deactivate':
        qs.update(ativo=False)
    elif action == 'delete':
        qs.delete()
    else:
        return HttpResponseBadRequest('Ação inválida.')

    return JsonResponse({'ok': True})


@login_required
@user_passes_test(is_admin)
@require_POST
def api_personal_toggle(request, pk:int):
    p = get_object_or_404(Personal, pk=pk)
    p.ativo = not p.ativo
    p.save(update_fields=['ativo'])
    return JsonResponse({'ok': True, 'is_active': p.ativo})


@login_required
@user_passes_test(is_admin)
@require_POST
def api_personal_delete(request, pk:int):
    p = get_object_or_404(Personal, pk=pk)
    p.delete()
    return JsonResponse({'ok': True})


# ====== VIEWS “NORMAIS” para gerenciar personal (opcional) ======

@login_required
@require_http_methods(["GET", "POST"])
@user_passes_test(is_admin)
def gerenciar_personal(request):
    # ações em massa
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

    # listagem
    q      = request.GET.get("q", "").strip()
    sex    = request.GET.get("sex", "")
    status = request.GET.get("status", "")

    people = Personal.objects.all().order_by("-id")

    if q:
        people = people.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)  |
            Q(email__icontains=q)      |
            Q(cpf__icontains=q)        |
            Q(cref__icontains=q)
        )
    if sex:
        people = people.filter(sex=sex)
    if status == "active":
        people = people.filter(ativo=True)
    elif status == "inactive":
        people = people.filter(ativo=False)

    paginator = Paginator(people, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    ctx = {"page_obj": page_obj, "q": q, "sex": sex, "status": status}
    return render(request, "global/gerenciar_personal.html", ctx)
