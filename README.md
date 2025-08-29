# 🏋️ Sistema de Academia — UNILIFE

Um sistema web desenvolvido em **Django** para gerenciamento de academias, permitindo o cadastro de **Alunos**, **Personais** e **Proprietário**, com acesso diferenciado de acordo com o tipo de usuário.

## 🚀 Funcionalidades

### 👥 Usuários
- Cadastro de **Alunos** (com CPF, telefone, data de nascimento e restrições médicas).
- Cadastro de **Personais** (feito pelo proprietário, com validação de CREF).
- Login via **CPF + senha**.
- Redirecionamento automático do usuário para a área correspondente (**Aluno, Personal ou Proprietário**).
- Logout seguro com redirecionamento para a tela de login.
- Recuperação e redefinição de senha.

### 📊 Alunos
- Visualizar treinos atribuídos por Personais.
- Visualizar perfil e atualizar dados.
- Agendar anamnese.
- Redefinir senha.

### 🏋️ Personais
- Criar treinos.
- Atribuir treinos a alunos.
- Gerenciar treinos existentes.
- Gerenciar alunos existentes.
- Registrar/avaliar anamnese de alunos.
- Anexar anamnese a alunos.
- Redefinir senha.

### 🛠️ Proprietário
- Cadastrar e remover Personais.
- Gerenciar cadastros (alunos e personais).
- Editar ou remover cadastros.
- Criar treinos.
- Atribuir treinos a alunos.
- Gerenciar treinos existentes.
- Gerenciar alunos existentes.
- Registrar/avaliar anamnese de alunos.
- Anexar anamnese a alunos.
- Redefinir senha.
  
---

## 🗂️ Modelagem

### Entidades principais
- **User (Django Auth)** → login por CPF (username).
- **Cadastro** → perfil do usuário com informações complementares.
- **Aluno** → perfil estendido de Cadastro.
- **Personal** → perfil estendido de Cadastro (com CREF).
- **Treino** → criado por personal ou proprietário, atribuído a alunos.
- **Anamnese** → histórico médico/anamnese de alunos.
- **Agendamento** → marcação de avaliações/anamneses entre Aluno e Personal/Proprietário.

### Relacionamentos
- `User 1—1 Cadastro`
- `Cadastro 1—1 Aluno | Personal`
- `Personal 1—N Treino`
- `Aluno N—N Treino`
- `Aluno 1—N Anamnese`
- `Personal 1—N Anamnese`
- `Aluno 1—N Agendamento`
- `Personal 1—N Agendamento`

---

## 💻 Tecnologias Utilizadas

- **Backend**: [Django 5.x](https://www.djangoproject.com/)
- **Banco de Dados**: SQLite (dev) / PostgreSQL (prod)
- **Frontend**: HTML5 + CSS3 customizado
- **Autenticação**: Django Auth com CPF como username
- **Diagramação**: UML (casos de uso + classes)

---

## ⚙️ Instalação e Execução

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/academia-unilife.git
   cd academia-unilife

2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/Mac
   .venv\Scripts\activate      # Windows

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   
4. Realize as migrações:
   ```bash
   python manage.py migrate

5. Crie um superusuário (Proprietário):
   ```bash
   python manage.py createsuperuser
   
6. Execute o servidor:
   ```bash
   python manage.py runserver
   
7. Acesse no navegador:
   ```bash
   http://127.0.0.1:8000

---

## 🔐 Login e Perfis

- Aluno: cadastra-se diretamente no sistema.
- Personal: cadastrado pelo proprietário (necessário informar CREF).
- Proprietário: usuário administrador criado via createsuperuser.

---

## 📌 Roadmap (Próximos Passos)
-  Upload de arquivos de anamnese (PDF, imagens).
- Painel administrativo personalizado.
- Notificações por e-mail (confirmação de cadastro e agendamento).
- API REST com Django Rest Framework (para integração com app mobile).

---

## 📝 Licença

Este projeto está sob a licença MIT.
Sinta-se livre para usar, modificar e distribuir.
