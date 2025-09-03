# contas/admin.py
from django.contrib import admin
from django.contrib.auth.models import User
from .models import Aluno, Personal, Admin as Proprietario, Treino, Anamnese

# --- Utilitário: auto-atribuir o responsável (usuário logado) ---
class SetResponsavelMixin:
    def save_model(self, request, obj, form, change):
        if hasattr(obj, "responsavel") and obj.responsavel_id is None:
            obj.responsavel = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for inst in instances:
            if isinstance(inst, Anamnese) and inst.responsavel_id is None:
                inst.responsavel = request.user
            inst.save()
        formset.save_m2m()

# --- Inline de Anamnese dentro do Aluno ---
class AnamneseInline(SetResponsavelMixin, admin.StackedInline):
    model = Anamnese
    extra = 0
    fields = (
        "data",
        "peso", "altura",
        "historico_medico", "restricoes", "observacoes",
        "responsavel", "atualizado_em",
    )
    readonly_fields = ("data", "atualizado_em")
    classes = ("collapse",)

# --- Admins principais ---
@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    inlines = [AnamneseInline]
    list_display = ("id", "first_name", "last_name", "username_cpf", "tel", "sex", "email", "created_at")
    search_fields = ("first_name", "last_name", "user__username", "email", "tel")
    list_filter = ("sex", "created_at")
    ordering = ("-created_at",)

    @admin.display(description="CPF (username)")
    def username_cpf(self, obj: Aluno):
        return obj.user.username

@admin.register(Personal)
class PersonalAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "username_cpf", "cref", "tel", "sex", "email", "ativo", "created_at")
    search_fields = ("first_name", "last_name", "user__username", "cref", "email", "tel")
    list_filter = ("ativo", "sex", "created_at")
    ordering = ("-created_at",)

    @admin.display(description="CPF (username)")
    def username_cpf(self, obj: Personal):
        return obj.user.username

@admin.register(Proprietario)
class AdminPerfilAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "username_cpf", "cargo", "tel", "email", "created_at")
    search_fields = ("first_name", "last_name", "user__username", "email", "tel", "cargo")
    list_filter = ("created_at",)
    ordering = ("-created_at",)

    @admin.display(description="CPF (username)")
    def username_cpf(self, obj: Proprietario):
        return obj.user.username

# --- Admin de Treino ---
@admin.register(Treino)
class TreinoAdmin(admin.ModelAdmin):
    list_display = ("id", "titulo", "criado_por", "created_at")
    search_fields = ("titulo", "descricao", "criado_por__username", "criado_por__first_name", "criado_por__last_name")
    list_filter = ("created_at",)
    filter_horizontal = ("alunos",)
    ordering = ("-created_at",)

# --- Admin de Anamnese ---
@admin.register(Anamnese)
class AnamneseAdmin(SetResponsavelMixin, admin.ModelAdmin):
    list_display = ("id", "aluno", "responsavel", "data", "peso", "altura")
    search_fields = (
        "aluno__first_name", "aluno__last_name", "aluno__user__username",
        "responsavel__username", "responsavel__first_name", "responsavel__last_name",
    )
    list_filter = ("data",)
    readonly_fields = ("data", "atualizado_em")
    fields = (
        "aluno", "responsavel",
        "data", "atualizado_em",
        "peso", "altura",
        "historico_medico", "restricoes", "observacoes",
    )
    ordering = ("-data",)
