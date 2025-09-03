from django.db import models
from django.contrib.auth.models import User


# Marcas de tempo padrão
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# Campos comuns aos 3 perfis
class PerfilBase(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="%(class)s")

    first_name = models.CharField(max_length=254)
    last_name  = models.CharField(max_length=254, blank=True)
    tel        = models.CharField(max_length=11)  # DDD + número (apenas dígitos)
    SEX_CHOICES = [('M', 'Masculino'), ('F', 'Feminino'), ('O', 'Outro')]
    sex = models.CharField(max_length=1, choices=SEX_CHOICES)
    email = models.EmailField()
    date_of_birth = models.DateField()

    class Meta:
        abstract = True

    def __str__(self):
        # username = CPF (só dígitos)
        return f"{self.first_name} ({self.user.username})"


class Aluno(PerfilBase):
    pass


class Personal(PerfilBase):
    # CREF só existe em personal
    cref = models.CharField(max_length=20)  # permite formatos como "CREF 12345-G/SP"
    ativo = models.BooleanField(default=True)


class Admin(PerfilBase):
    cargo = models.CharField(max_length=50, blank=True, default="Proprietário")


class Treino(TimeStampedModel):
    titulo = models.CharField(max_length=120)
    descricao = models.TextField(blank=True)
    criado_por = models.ForeignKey(User, on_delete=models.PROTECT, related_name="treinos_criados")
    # N–N com Aluno (um treino para vários alunos e vice-versa)
    alunos = models.ManyToManyField(Aluno, related_name="treinos", blank=True)

    def __str__(self):
        return self.titulo

    def is_criador_personal(self):
        return hasattr(self.criado_por, "personal")

    def is_criador_admin(self):
        return hasattr(self.criado_por, "admin")

class Anamnese(models.Model):
    aluno = models.ForeignKey(
        Aluno, 
        on_delete=models.CASCADE, 
        related_name="anamneses"
    )
    responsavel = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name="anamneses_realizadas"
    )
    data = models.DateTimeField(auto_now_add=True)

    # Campos médicos básicos
    peso = models.DecimalField(max_digits=5, decimal_places=2, help_text="kg")
    altura = models.DecimalField(max_digits=4, decimal_places=2, help_text="m")
    
    # Histórico do aluno
    historico_medico = models.TextField(blank=True)
    restricoes = models.TextField(blank=True)
    observacoes = models.TextField(blank=True)

    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Anamnese"
        verbose_name_plural = "Anamneses"
        ordering = ["-data"]

    def __str__(self):
        return f"Anamnese de {self.aluno.first_name} em {self.data.strftime('%d/%m/%Y')}"