from django.urls import path
from django.contrib.auth import views as auth_views
from .views import CPFLoginView, registrar, recuperar_senha_view, home_admin, home_aluno, home_personal, home_redirect, cadastrar_personal

urlpatterns = [
    path('', CPFLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('registrar/', registrar, name='registrar'),
    path('senha/', recuperar_senha_view, name='recuperar-senha'),
    path('admin/personais/novo/', cadastrar_personal, name='cadastrar-personal'),


    # Rota neutra que decide o destino por perfil
    path('home/', home_redirect, name='home'),
    
    # Homes específicas
    path("aluno/home/", home_aluno, name="home-aluno"),
    path("personal/home/", home_personal, name="home-personal"),
    path("admin/home/", home_admin, name="home-admin"),
]
