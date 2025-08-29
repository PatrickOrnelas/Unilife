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
- Anexar anamnese.
- Redefinir senha.

### 🏋️ Personais
- Criar treinos.
- Atribuir treinos a alunos.
- Gerenciar treinos existentes.
- Registrar/avaliar anamnese de alunos.

### 🛠️ Proprietário
- Cadastrar e remover Personais.
- Gerenciar cadastros (alunos e personais).
- Editar ou remover cadastros.

---

## 🗂️ Modelagem

### Entidades principais
- **User (Django Auth)** → login por CPF (username).
- **Cadastro** → perfil do usuário com informações complementares.
- **Aluno** → perfil estendido de Cadastro.
- **Personal** → perfil estendido de Cadastro (com CREF).
- **Treino** → criado por personal, atribuído a alunos.
- **Anamnese** → histórico médico/anamnese de alunos.
- **Agendamento** → marcação de avaliações/anamneses entre Aluno e Personal.

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


---

## ⚙️ Instalação e Execução

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/academia-unilife.git
   cd academia-unilife


