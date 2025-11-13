from django.db import models
from django.contrib.auth.models import User

class Aluno(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="aluno")
    cpf = models.CharField(max_length=14, unique=True, db_index=True)  # 000.000.000-00
    first_name = models.CharField(max_length=254)
    last_name = models.CharField(max_length=254, blank=True)
    tel = models.CharField(max_length=11)  # DDD + número (apenas dígitos)
    SEX_CHOICES = [('M', 'Masculino'), ('F', 'Feminino'), ('O', 'Outro')]
    sex = models.CharField(max_length=1, choices=SEX_CHOICES)
    email = models.EmailField()
    date_of_birth = models.DateField()
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    photo = models.ImageField(upload_to='alunos/photos/', blank=True, null=True)

    class Meta:
        verbose_name = "Aluno"
        verbose_name_plural = "Alunos"

    def __str__(self):
        return f"{self.first_name} ({self.user.username})"


class Personal(models.Model):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="personal")
    cpf = models.CharField(max_length=14, unique=True, db_index=True)
    first_name = models.CharField(max_length=254)
    last_name = models.CharField(max_length=254, blank=True)
    tel = models.CharField(max_length=11)
    SEX_CHOICES = [('M', 'Masculino'), ('F', 'Feminino'), ('O', 'Outro')]
    sex = models.CharField(max_length=1, choices=SEX_CHOICES)
    email = models.EmailField()
    date_of_birth = models.DateField()
    cref = models.CharField(max_length=20, unique=True, blank=True, null=True)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    photo = models.ImageField(upload_to='personals/photos/', blank=True, null=True)

    class Meta:
        verbose_name = "Personal"
        verbose_name_plural = "Personais"
    
    def __str__(self):
        return f"{self.first_name} ({self.user.username})"


class Proprietario(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="proprietario")
    cpf = models.CharField(max_length=14, unique=True, db_index=True)
    first_name = models.CharField(max_length=254)
    last_name = models.CharField(max_length=254, blank=True)
    tel = models.CharField(max_length=11)  # DDD + número (apenas dígitos)
    SEX_CHOICES = [('M', 'Masculino'), ('F', 'Feminino'), ('O', 'Outro')]
    sex = models.CharField(max_length=1, choices=SEX_CHOICES)
    email = models.EmailField()
    date_of_birth = models.DateField()
    cargo = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    photo = models.ImageField(upload_to='proprietarios/photos/', blank=True, null=True)

    class Meta:
        verbose_name = "Proprietário"
        verbose_name_plural = "Proprietários"

    def __str__(self):
        return f"{self.first_name} ({self.user.username})"



class Treino(models.Model):
    titulo = models.CharField(max_length=120)
    descricao = models.TextField(blank=True)
    criado_por = models.ForeignKey(User, on_delete=models.PROTECT, related_name="treinos_criados")
    # M2M simples (sem through) => compatível com filter_horizontal no admin
    alunos = models.ManyToManyField(Aluno, related_name="treinos", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titulo

    def is_criador_personal(self):
        return hasattr(self.criado_por, "personal")

    def is_criador_admin(self):
        return hasattr(self.criado_por, "admin")


class Anamnese(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name="anamneses")
    responsavel = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="anamneses_realizadas"
    )
    data = models.DateTimeField(auto_now_add=True)
    peso = models.DecimalField(max_digits=5, decimal_places=2, help_text="kg")
    altura = models.DecimalField(max_digits=4, decimal_places=2, help_text="m")
    historico_medico = models.TextField(blank=True)
    restricoes = models.TextField(blank=True)
    observacoes = models.TextField(blank=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Anamnese"
        verbose_name_plural = "Anamneses"
        ordering = ["-data"]

    def __str__(self):
        return f"Anamnese para {self.aluno.first_name} em {self.data.strftime('%Y-%m-%d')}"
