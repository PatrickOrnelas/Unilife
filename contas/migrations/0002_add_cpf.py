from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('contas', '0001_initial'),   # mantém o que você já tem
    ]

    operations = [
        # Adiciona CPF nas três tabelas que herdam de PerfilBase
        migrations.AddField(
            model_name='admin',
            name='cpf',
            field=models.CharField(
                max_length=14,
                unique=True,
                db_index=True,
                null=True, blank=True,   # permite migrar dados existentes
            ),
        ),
        migrations.AddField(
            model_name='aluno',
            name='cpf',
            field=models.CharField(
                max_length=14,
                unique=True,
                db_index=True,
                null=True, blank=True,
            ),
        ),
        migrations.AddField(
            model_name='personal',
            name='cpf',
            field=models.CharField(
                max_length=14,
                unique=True,
                db_index=True,
                null=True, blank=True,
            ),
        ),
    ]
