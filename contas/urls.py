# contas/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    CPFLoginView, registrar, recuperar_senha_view,
    home_admin, home_aluno, home_personal, home_redirect,
    cadastrar_personal, gerenciar_personal,
    personal_edit,
    personal_toggle, personal_delete,
    change_password,  # <- nova rota
    workouts_create,
    workouts_list,
    workouts_get,
    workouts_edit,
    workouts_toggle,
    workouts_delete,
    workouts_duplicate,
    students_search,
    workouts_assign,
    api_personals_list, api_personal_toggle, api_personal_delete, api_personals_bulk,
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

    # API Treinos
    path("workouts/create/", workouts_create, name="workout-create"),
    path("workouts/list/", workouts_list, name="workout-list"),
    path("workouts/<int:pk>/", workouts_get, name="workout-get"),
    path("workouts/<int:pk>/edit/", workouts_edit, name="workout-edit"),
    path("workouts/<int:pk>/toggle/", workouts_toggle, name="workout-toggle"),
    path("workouts/<int:pk>/delete/", workouts_delete, name="workout-delete"),
    path("workouts/<int:pk>/duplicate/", workouts_duplicate, name="workout-duplicate"),
    path("students/search/", students_search, name="students-search"),
    path("workouts/assign/", workouts_assign, name="workout-assign"),

    # Gerenciamento de Personais
    path('admin/personais/novo/', cadastrar_personal, name='cadastrar-personal'),
    path('admin/personais/', gerenciar_personal, name='gerenciar-personal'),
    path('admin/personais/<int:pk>/edit/', personal_edit, name='personal-edit'),
    path('admin/personais/<int:pk>/toggle/', personal_toggle, name='personal-toggle'),
    path('admin/personais/<int:pk>/delete/', personal_delete, name='personal-delete'),

    # API Personais
    path('api/personals/', api_personals_list, name='api-personals-list'),
    path('api/personals/bulk/', api_personals_bulk, name='api-personals-bulk'),
    path('api/personals/<int:pk>/toggle/', api_personal_toggle, name='api-personal-toggle'),
    path('api/personals/<int:pk>/delete/', api_personal_delete, name='api-personal-delete'),

    # Perfil / Segurança
    path('conta/alterar-senha/', change_password, name='change-password'),
]
