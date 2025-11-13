# contas/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    CPFLoginView, registrar, recuperar_senha_view,
    home_admin, home_aluno, home_personal, home_redirect,
    cadastrar_personal, gerenciar_personal,
    personal_toggle, personal_delete,
    change_password,  # <- nova rota
)

urlpatterns = [
    # Auth
    path('', CPFLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('registrar/', registrar, name='registrar'),
    path('senha/', recuperar_senha_view, name='recuperar-senha'),

# Rota neutra que decide o destino por perfil
    path('home/', home_redirect, name='home'),

# Personal URLs
    path("personal/home/", home_personal, name="home-personal"),
    
    path("personal/treinos/", home_personal, name="gerenciar-treinos"),

 # Aluno URLs
    path("aluno/home/", home_aluno, name="home-aluno"),

# Proprietario URLs
    path("admin/home/", home_admin, name="home-admin"),
    path("admin/alunos/", home_admin, name="gerenciar-alunos"),
    path("admin/treinos/", home_admin, name="gerenciar-treinos"),
    path("admin/treinos/novo/", home_admin, name="criar-treinos"),

    # Gerenciamento de Personais
    path('admin/personais/novo/', cadastrar_personal, name='cadastrar-personal'),
    path('admin/personais/', gerenciar_personal, name='gerenciar-personal'),
    path('admin/personais/<int:pk>/toggle/', personal_toggle, name='personal-toggle'),
    path('admin/personais/<int:pk>/delete/', personal_delete, name='personal-delete'),

    # Perfil / Segurança
    path('conta/alterar-senha/', change_password, name='change-password'),
]
