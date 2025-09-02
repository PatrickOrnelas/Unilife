from django.urls import path
from django.contrib.auth import views as auth_views
from .views import CPFLoginView, registrar, home, recuperar_senha_view

urlpatterns = [
    path('home/', home, name='home'),
    path('', CPFLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('registrar/', registrar, name='registrar'),
    path('senha/', recuperar_senha_view, name='recuperar-senha'),
]
