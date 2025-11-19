# contas/views.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, update_session_auth_hash
from django.urls import reverse_lazy
from django.conf import settings
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.views import LoginView
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.urls import reverse

from .forms import LoginForm, RegistroAlunoForm, RegistroPersonalForm, PersonalEditForm
from .models import Personal, Aluno, Proprietario, Treino


def destino_por_perfil(user):
    # usa os relacionamentos OneToOne existentes nos modelos
    if getattr(user, "proprietario", None) is not None or getattr(user, "is_proprietario", False):
        return reverse_lazy("home-admin")
    if getattr(user, "personal", None) is not None or getattr(user, "is_treinador", False) or getattr(user, "is_personal", False):
        return reverse_lazy("home-personal")
    if getattr(user, "aluno", None) is not None or getattr(user, "is_aluno", False):
        return reverse_lazy("home-aluno")
    return reverse_lazy("home")  # fallback


class CPFLoginView(LoginView):
    template_name = "global/login.html"
    authentication_form = LoginForm

    def get_success_url(self):
        return destino_por_perfil(self.request.user)


@login_required
def home_redirect(request):
    """Redireciona para a home correta com base no tipo do usuário."""
    return redirect(destino_por_perfil(request.user))


@login_required
def home_aluno(request):
    aluno = getattr(request.user, "aluno", None)
    treinos = Treino.objects.filter(alunos=aluno, is_active=True).order_by("-updated_at") if aluno else Treino.objects.none()
    return render(request, "global/aluno/home_aluno.html", {"treinos": treinos})


@login_required
def home_personal(request):
    return render(request, "global/personal/home_personal.html")


@login_required
def home_admin(request):
    return render(request, "global/proprietario/home_admin.html")


def login_view(request):
    # Mantido apenas se você quiser uma view manual simples.
    from django.contrib.auth.forms import AuthenticationForm
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        # AuthenticationForm já autentica, então basta logar
        auth_login(request, user)
        return redirect(destino_por_perfil(user))
    return render(request, 'global/login.html', {'form': form})


def registrar(request):
    form = RegistroAlunoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()  # O form deve criar e retornar um User
        raw_password = form.cleaned_data.get("password1")

        # tente autenticar via backends configurados
        user_auth = authenticate(request, username=getattr(user, "username", None), password=raw_password)
        if user_auth:
            auth_login(request, user_auth)
        else:
            # quando há múltiplos backends, defina explicitamente o backend no user antes de login
            backend = settings.AUTHENTICATION_BACKENDS[0]
            user.backend = backend
            auth_login(request, user)

        return redirect(destino_por_perfil(user))
    return render(request, 'global/registrar.html', {'form': form})


def recuperar_senha_view(request):
    return render(request, 'global/reset_password.html')


def is_admin(user):
    # proprietario é o "admin" do sistema
    return getattr(user, "proprietario", None) is not None or getattr(user, "is_proprietario", False)


# --------- Personais (views normais, sem API) ---------

@login_required
@user_passes_test(is_admin)
def cadastrar_personal(request):
    """Cadastro de personal com senha automática - mantém na mesma página após sucesso"""
    form_action = reverse('cadastrar-personal')

    if request.method == "POST":
        form = RegistroPersonalForm(request.POST)
        if form.is_valid():
            # Salvar e obter o personal criado
            personal = form.save()
            # Gerar a senha para mostrar na mensagem
            senha_gerada = personal.first_name.capitalize() + "123"
            messages.success(request, f"Personal cadastrado com sucesso! Senha gerada: {senha_gerada}")
            
            # Limpar o formulário criando um novo formulário vazio
            form = RegistroPersonalForm()
    else:
        # GET: mostrar formulário vazio
        form = RegistroPersonalForm()
    
    context = {
        'form': form,
        'form_action': form_action,
    }
    return render(request, "global/proprietario/cadastrar_personal.html", context)

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

    return render(request, "global/proprietario/home_admin.html", {
        "page_obj": page_obj,
        "q": q, "sex": sex, "status": status
    })


@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def personal_edit(request, pk):
    p = get_object_or_404(Personal, pk=pk)
    if request.method == "POST":
        form = PersonalEditForm(request.POST, instance=p)
        if form.is_valid():
            form.save()
            messages.success(request, "Personal atualizado com sucesso.")
            # permanece na página de edição
        else:
            messages.error(request, "Corrija os erros do formulário.")
    else:
        form = PersonalEditForm(instance=p)
    context = {
        "form": form,
        "personal": p,
        "form_action": reverse("personal-edit", args=[p.id]),
    }
    return render(request, "global/proprietario/cadastrar_personal.html", context)


# --------- API: Personais ---------

@login_required
@user_passes_test(is_admin)
def api_personals_list(request):
    q = (request.GET.get("q") or "").strip()
    sex = (request.GET.get("sex") or "").strip()
    status = (request.GET.get("status") or "").strip()
    page = int(request.GET.get("page") or 1)
    page_size = int(request.GET.get("page_size") or 10)

    qs = Personal.objects.all().order_by("-created_at")
    if q:
        qs = qs.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q) |
            Q(cpf__icontains=q) |
            Q(cref__icontains=q)
        )
    if sex in ("M", "F", "O"):
        qs = qs.filter(sex=sex)
    if status == "active":
        qs = qs.filter(ativo=True)
    elif status == "inactive":
        qs = qs.filter(ativo=False)

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)

    def row(p: Personal):
        return {
            "id": p.id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "cpf": p.cpf,
            "cref": p.cref,
            "tel": p.tel,
            "sex": p.sex,
            "email": p.email,
            "is_active": bool(p.ativo),
            "created_at": p.created_at.isoformat(),
        }

    return JsonResponse({
        "ok": True,
        "count": paginator.count,
        "page": page_obj.number,
        "num_pages": paginator.num_pages,
        "results": [row(p) for p in page_obj.object_list],
    })


@login_required
@user_passes_test(is_admin)
@require_POST
def api_personal_toggle(request, pk):
    p = get_object_or_404(Personal, pk=pk)
    p.ativo = not p.ativo
    p.save(update_fields=["ativo", "updated_at"])
    return JsonResponse({"ok": True, "is_active": p.ativo})


@login_required
@user_passes_test(is_admin)
@require_POST
def api_personal_delete(request, pk):
    p = get_object_or_404(Personal, pk=pk)
    p.delete()
    return JsonResponse({"ok": True})


@login_required
@user_passes_test(is_admin)
@require_POST
def api_personals_bulk(request):
    import json
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)
    action = (payload.get("action") or "").strip()
    ids = payload.get("ids") or []
    if not ids:
        return JsonResponse({"ok": False, "error": "no_ids"}, status=400)
    qs = Personal.objects.filter(pk__in=ids)
    if action == "activate":
        qs.update(ativo=True)
    elif action == "deactivate":
        qs.update(ativo=False)
    elif action == "delete":
        qs.delete()
    else:
        return JsonResponse({"ok": False, "error": "invalid_action"}, status=400)
    return JsonResponse({"ok": True})


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
    if getattr(request.user, "proprietario", None) is not None or getattr(request.user, "is_proprietario", False):
        resp = redirect("home-admin")
        resp["Location"] += "#perfil"
        return resp
    # fallback: volta para sua home padrão
    return redirect("home")

def criar_treinos(request):
    return render(request, "global/personal/home_personal.html")


@login_required
@user_passes_test(is_admin)
@require_POST
def workouts_create(request):
    import json
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)

    name = (payload.get("name") or "Treino").strip()
    day = (payload.get("day") or "").strip()
    items = payload.get("items")

    if not isinstance(items, list) or not items:
        return JsonResponse({"ok": False, "error": "items_required"}, status=400)

    t = Treino.objects.create(
        titulo=name,
        descricao="",
        criado_por=request.user,
        dia=day,
        items=items,
    )

    return JsonResponse({"ok": True, "workout_id": t.id})


@login_required
@user_passes_test(is_admin)
def workouts_list(request):
    q = (request.GET.get("q") or "").strip()
    day = (request.GET.get("day") or "").strip()
    status = (request.GET.get("status") or "").strip()
    page = int(request.GET.get("page") or 1)
    page_size = int(request.GET.get("page_size") or 10)

    qs = Treino.objects.all().order_by("-updated_at")
    if q:
        qs = qs.filter(
            Q(titulo__icontains=q) |
            Q(alunos__first_name__icontains=q) |
            Q(alunos__email__icontains=q)
        )
    if day:
        qs = qs.filter(dia=day)
    if status == "active":
        qs = qs.filter(is_active=True)
    elif status == "inactive":
        qs = qs.filter(is_active=False)
    qs = qs.distinct()

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)

    def row(t: Treino):
        a = t.alunos.first()
        return {
            "id": t.id,
            "name": t.titulo,
            "day": t.dia or "",
            "items_count": (len(t.items) if isinstance(t.items, list) else 0),
            "is_active": bool(t.is_active),
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat(),
            "student_name": (a.first_name if a else None),
            "student_email": (a.email if a else None),
        }

    data = {
        "ok": True,
        "count": paginator.count,
        "page": page_obj.number,
        "num_pages": paginator.num_pages,
        "results": [row(t) for t in page_obj.object_list],
    }
    return JsonResponse(data)


@login_required
@user_passes_test(is_admin)
def workouts_get(request, pk):
    t = get_object_or_404(Treino, pk=pk)
    a = t.alunos.first()
    data = {
        "id": t.id,
        "name": t.titulo,
        "day": t.dia or "",
        "items": (t.items if isinstance(t.items, list) else []),
        "is_active": bool(t.is_active),
        "student": {
            "id": (a.id if a else None),
            "name": (a.first_name if a else None),
            "email": (a.email if a else None),
        },
    }
    return JsonResponse({"ok": True, "workout": data})


@login_required
@user_passes_test(is_admin)
@require_POST
def workouts_edit(request, pk):
    t = get_object_or_404(Treino, pk=pk)
    import json
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)
    name = (payload.get("name") or "Treino").strip()
    day = (payload.get("day") or "").strip()
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        return JsonResponse({"ok": False, "error": "items_required"}, status=400)
    t.titulo = name
    t.dia = day
    t.items = items
    t.save(update_fields=["titulo", "dia", "items", "updated_at"])
    return JsonResponse({"ok": True, "workout_id": t.id})


@login_required
@user_passes_test(is_admin)
@require_POST
def workouts_toggle(request, pk):
    t = get_object_or_404(Treino, pk=pk)
    t.is_active = not t.is_active
    t.save(update_fields=["is_active", "updated_at"])
    return JsonResponse({"ok": True, "is_active": t.is_active})


@login_required
@user_passes_test(is_admin)
@require_POST
def workouts_delete(request, pk):
    t = get_object_or_404(Treino, pk=pk)
    t.delete()
    return JsonResponse({"ok": True})


@login_required
@user_passes_test(is_admin)
@require_POST
def workouts_duplicate(request, pk):
    t = get_object_or_404(Treino, pk=pk)
    clone = Treino.objects.create(
        titulo=f"{t.titulo} (Cópia)",
        descricao=t.descricao,
        criado_por=request.user,
        dia=t.dia,
        items=t.items,
        is_active=t.is_active,
    )
    return JsonResponse({"ok": True, "workout_id": clone.id})


@login_required
@user_passes_test(is_admin)
def students_search(request):
    q = (request.GET.get("q") or "").strip()
    qs = Aluno.objects.all().order_by("first_name")
    if q:
        qs = qs.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q)
        )
    data = {
        "ok": True,
        "results": [
            {"id": a.id, "name": a.first_name, "email": a.email}
            for a in qs[:20]
        ]
    }
    return JsonResponse(data)


@login_required
@user_passes_test(is_admin)
@require_POST
def workouts_assign(request):
    import json
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)
    workout_id = payload.get("workout_id")
    aluno_id = payload.get("aluno_id")
    if not workout_id or not aluno_id:
        return JsonResponse({"ok": False, "error": "missing_params"}, status=400)
    t = get_object_or_404(Treino, pk=int(workout_id))
    a = get_object_or_404(Aluno, pk=int(aluno_id))
    t.alunos.add(a)
    return JsonResponse({"ok": True})
