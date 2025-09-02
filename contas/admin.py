# contas/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Aluno, Personal, Admin as AdminPerfil, Treino


# --------- Mixins/Helpers ---------
class PerfilBaseAdmin(admin.ModelAdmin):
    """
    Configuração base para Aluno/Personal/Admin:
    - lista com nome, CPF (username), e-mail, sexo, data de nasc.
    - busca por CPF (user__username), nome e e-mail
    """
    list_display = (
        "nome_completo",
        "cpf",
        "email",
        "sex",
        "date_of_birth",
        "created_at",
    )
    list_select_related = ("user",)
    search_fields = (
        "user__username",      # CPF
        "first_name",
        "last_name",
        "email",
    )
    list_filter = ("sex",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Nome")
    def nome_completo(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    @admin.display(description="CPF")
    def cpf(self, obj):
        return obj.user.username

    @admin.display(description="Criado em")
    def created_at(self, obj):
        return obj.created_at


# --------- Aluno ---------
@admin.register(Aluno)
class AlunoAdmin(PerfilBaseAdmin):
    fieldsets = (
        ("Vinculação", {"fields": ("user",)}),
        ("Dados pessoais", {
            "fields": (
                "first_name", "last_name", "email", "tel",
                "sex", "date_of_birth", "restrictions",
            )
        }),
        ("Metadados", {"fields": ("created_at", "updated_at")}),
    )


# --------- Personal ---------
@admin.register(Personal)
class PersonalAdmin(PerfilBaseAdmin):
    list_display = PerfilBaseAdmin.list_display + ("cref", "ativo")
    list_filter = PerfilBaseAdmin.list_filter + ("ativo",)
    search_fields = PerfilBaseAdmin.search_fields + ("cref",)

    fieldsets = (
        ("Vinculação", {"fields": ("user",)}),
        ("Dados pessoais", {
            "fields": (
                "first_name", "last_name", "email", "tel",
                "sex", "date_of_birth", "restrictions",
            )
        }),
        ("Profissional", {"fields": ("cref", "ativo")}),
        ("Metadados", {"fields": ("created_at", "updated_at")}),
    )


# --------- Admin (Proprietário) ---------
@admin.register(AdminPerfil)
class AdminPerfilAdmin(PerfilBaseAdmin):
    list_display = PerfilBaseAdmin.list_display + ("cargo",)
    search_fields = PerfilBaseAdmin.search_fields + ("cargo",)

    fieldsets = (
        ("Vinculação", {"fields": ("user",)}),
        ("Dados pessoais", {
            "fields": (
                "first_name", "last_name", "email", "tel",
                "sex", "date_of_birth", "restrictions",
            )
        }),
        ("Organizacional", {"fields": ("cargo",)}),
        ("Metadados", {"fields": ("created_at", "updated_at")}),
    )


# --------- Treino ---------
@admin.register(Treino)
class TreinoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "criador", "alunos_count", "created_at")
    search_fields = ("titulo", "descricao", "criado_por__first_name", "criado_por__last_name", "criado_por__username")
    list_filter = ()
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    # UI melhor para ManyToMany
    filter_horizontal = ("alunos",)

    fieldsets = (
        ("Informações", {"fields": ("titulo", "descricao")}),
        ("Relacionamentos", {"fields": ("criado_por", "alunos")}),
        ("Metadados", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Criado por")
    def criador(self, obj):
        u = obj.criado_por
        nome = (u.get_full_name() or u.username).strip()
        return f"{nome} (CPF: {u.username})"

    @admin.display(description="Alunos")
    def alunos_count(self, obj):
        return obj.alunos.count()
