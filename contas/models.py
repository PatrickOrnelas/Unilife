from django.db import models
from django.contrib.auth.models import User

class Cadastros(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cadastros")

    first_name = models.CharField(max_length=254)
    last_name  = models.CharField(max_length=254, blank=True)
    cpf        = models.CharField(max_length=11, unique=True)  # só dígitos
    cref       = models.CharField(max_length=11, default="00000000000")
    tel        = models.CharField(max_length=11)               # DDD + número
    SEX_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
        ('O', 'Outro'),
    ]
    sex = models.CharField(max_length=1, choices=SEX_CHOICES)
    email = models.EmailField()

    date_of_birth = models.DateField()
    restrictions  = models.TextField(blank=True)

    type_user = models.CharField(max_length=8, default="ALUNO")

    create_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.first_name} ({self.cpf})'
    
class Treinos(models.Model):
    pass

class Alunos(models.Model):

    id_cadastro = models.OneToOneField(Cadastros, on_delete=models.CASCADE, related_name='alunos')
    id_treino = models.OneToOneField(Treinos, on_delete=models.CASCADE, related_name="treinos")

class Personais(models.Model):

    id_cadastro = models.OneToOneField(Cadastros, on_delete=models.CASCADE, related_name="personais")
    