from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy, reverse
from .forms import LoginForm, RegistroAlunoForm, RegistroPersonalForm
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_GET, require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404
import json
from .models import Personal
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST



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

from .forms import RegistroPersonalForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect

def is_admin(user):
    return hasattr(user, "admin")  # ou user.is_superuser, como preferir

@login_required
@user_passes_test(is_admin)
def cadastrar_personal(request):
    form = RegistroPersonalForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('admin:index')  # ou sua home de admin
    return render(request, 'global/admin_painel.html', {'form_personal': form})

# ========= GERENCIAR PERSONAL (API) =========

@login_required
@user_passes_test(is_admin)
@require_GET
def api_personals(request):
    """Lista filtrada/paginada para a tabela"""
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
        qs = qs.filter(is_active=(status == 'active'))

    # se não existir created_at no model, troque por '-id'
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
            'is_active':  getattr(p, 'is_active', True),
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
    """Ações em massa: activate | deactivate | delete"""
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return HttpResponseBadRequest('JSON inválido.')

    action = payload.get('action')
    ids    = payload.get('ids') or []
    qs     = Personal.objects.filter(id__in=ids)

    if action == 'activate':
        qs.update(is_active=True)
    elif action == 'deactivate':
        qs.update(is_active=False)
    elif action == 'delete':
        qs.delete()
    else:
        return HttpResponseBadRequest('Ação inválida.')

    return JsonResponse({'ok': True})

@login_required
@user_passes_test(is_admin)
@require_POST
def api_personal_toggle(request, pk:int):
    """Ativa/desativa um registro"""
    p = get_object_or_404(Personal, pk=pk)
    p.is_active = not p.is_active
    p.save(update_fields=['is_active'])
    return JsonResponse({'ok': True, 'is_active': p.is_active})

@login_required
@user_passes_test(is_admin)
@require_POST
def api_personal_delete(request, pk:int):
    """Remove um registro"""
    p = get_object_or_404(Personal, pk=pk)
    p.delete()
    return JsonResponse({'ok': True})

@login_required
def cadastrar_personal(request):
    if request.method == "POST":
        form = RegistroPersonalForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Personal cadastrado com sucesso!")
            return redirect("home-admin")  # ou para onde preferir
    else:
        form = RegistroPersonalForm()

    # use o caminho onde o template realmente está
    return render(
        request,
        "global/home_admin.html",         # <<<< AQUI é o ajuste
        {"form": form, "view": "cadastrar-personal"}  # (opcional: indica a aba)
    )

@login_required
@require_http_methods(["GET", "POST"])
def gerenciar_personal(request):
    # --- Ações em massa (POST) ---
    if request.method == "POST":
        action = request.POST.get("action")
        ids = request.POST.getlist("ids")
        qs = Personal.objects.filter(pk__in=ids)

        if not ids:
            messages.error(request, "Selecione pelo menos um registro.")
            return redirect("gerenciar-personal")

        if action == "activate":
            qs.update(is_active=True)
            messages.success(request, f"{qs.count()} personal(is) ativado(s).")
        elif action == "deactivate":
            qs.update(is_active=False)
            messages.success(request, f"{qs.count()} personal(is) desativado(s).")
        elif action == "delete":
            n = qs.count()
            qs.delete()
            messages.success(request, f"{n} personal(is) removido(s).")
        else:
            messages.error(request, "Ação inválida.")

        # volta mantendo filtros da URL
        return redirect(request.get_full_path())

    # --- Lista com filtros/paginação (GET) ---
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
    if sex:
        people = people.filter(sex=sex)
    if status == "active":
        people = people.filter(is_active=True)
    elif status == "inactive":
        people = people.filter(is_active=False)

    paginator = Paginator(people, 10)  # 10 por página
    page_obj = paginator.get_page(request.GET.get("page"))

    ctx = {"page_obj": page_obj, "q": q, "sex": sex, "status": status}
    return render(request, "global/gerenciar_personal.html", ctx)

@login_required
@require_POST
def personal_toggle(request, pk):
    p = get_object_or_404(Personal, pk=pk)
    p.is_active = not p.is_active
    p.save(update_fields=["is_active"])
    messages.success(request, f'{p.first_name} {"ativado" if p.is_active else "desativado"}.')
    return redirect(request.META.get("HTTP_REFERER", "gerenciar-personal"))

@login_required
@require_POST
def personal_delete(request, pk):
    p = get_object_or_404(Personal, pk=pk)
    p.delete()
    messages.success(request, "Personal removido.")
    return redirect(request.META.get("HTTP_REFERER", "gerenciar-personal"))