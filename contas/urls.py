from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CPFLoginView, registrar, home

urlpatterns = [
    path('home/', views.home, name='home'),
    path('', CPFLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('registrar/', views.registrar, name='registrar'),
    path('senha/', views.recuperar_senha_view, name='recuperar-senha')
]
