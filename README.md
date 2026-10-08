# Banco de Questões — Cursinho Popular Herbert de Souza

Sistema web para os professores do cursinho cadastrarem, organizarem e
acompanharem as questões que vão compor o **material didático próprio,
gratuito e livre** do cursinho. Feito em **Django**, roda local com
SQLite e em produção no **DigitalOcean App Platform**, com **PostgreSQL**
(Managed Database) e **Spaces** (imagens).

## Quer usar no seu cursinho?

Este projeto é livre para qualquer cursinho ou instituição usar e adaptar
para montar o próprio material didático. **Cada um roda na sua própria
infraestrutura**: você faz um fork, cria o **seu** app, o **seu** banco e o
**seu** Space no DigitalOcean (ou em outro provedor) e define as **suas**
variáveis de ambiente. O repositório não contém nenhuma chave, banco ou
bucket de ninguém — só código e arquivos de exemplo (`.env.example` e
`.do/app.yaml`, com placeholders).

Resumo do caminho: **fork → rodar local → criar sua infra → publicar**
(detalhes nas seções abaixo).

## O que o sistema faz

Todas as telas ficam no painel logado (menu lateral):

| Tela | Quem acessa | O que faz |
| --- | --- | --- |
| **Adicionar questões** | professores | Editor de texto rico (Quill) com imagens coladas/arrastadas e fórmulas em LaTeX (KaTeX), origem (vestibular ou autoria própria) e até 5 alternativas |
| **Ver questões** | todos | Lista de todas as questões do banco, com filtros por disciplina, assunto e texto |
| **Ver cronograma** | todos veem; só a coordenação edita | Calendário mensal com eventos de um ou vários dias (barras contínuas); a coordenação cria, edita e apaga |
| **Ver estatísticas** | todos | Painel de uma tela só: totais de questões e aulas, ranking e percentual de questões por disciplina, origem das questões e cobertura de conteúdo |
| **Ver planejamento** | cada professor vê só as suas frentes | Assuntos cadastrados por disciplina/frente e aula, com contagem de questões; cadastro de assunto em janela modal |
| **Colaboradores** | todos | Cards com foto, nome e função (Coordenador ou Professor de …) de cada pessoa |
| **Gerenciar professores** | só coordenação | Define quais frentes cada professor pode ver e cadastrar |
| **Ver perfil** | cada pessoa edita o seu | Nome completo, faculdade, foto e descrição — **aparecem impressos no material final** |

### Disciplinas, frentes e aulas

- Cada disciplina tem **frentes** (Frente A e B). Em Sociologia/Filosofia
  cada frente é a própria matéria; em Português as frentes são Gramática e
  Literatura; Redação tem uma frente única.
- Cada assunto pertence a uma **aula**: de 1 a 30, ou de 1 a 15 em
  Sociologia/Filosofia e Português.
- O professor só vê e cadastra assuntos/questões das frentes atribuídas a ele.
  A coordenação (superusuário) vê tudo.

### Acesso e login

- **Coordenação**: entra com usuário e senha.
- **Professores**: entram com o **número de celular** e a senha. A conta é
  criada com uma senha genérica combinada pela coordenação (no cursinho
  Herbert de Souza usamos `herbert123`; use a sua); no primeiro login o
  sistema obriga a cadastrar uma senha nova antes de liberar qualquer tela.

#### Cadastrando um professor novo (pelo `/admin/`)

1. **Autenticação e Autorização → Usuários → Adicionar usuário**: crie o
   usuário (nome interno) com a senha genérica combinada.
2. **Core → Perfis dos professores → Adicionar**: escolha o usuário, informe o
   **telefone** (com DDD, com ou sem máscara) e marque **Senha provisória**.
3. Em **Gerenciar professores** (menu do sistema), atribua as frentes dele.

## Rodando localmente

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # e ajuste se quiser

python manage.py migrate         # já cria as disciplinas e frentes
python manage.py createsuperuser # sua conta de coordenação
python manage.py runserver
```

Abra http://127.0.0.1:8000. Sem nada configurado no `.env`, o projeto usa
SQLite (`db.sqlite3`, ignorado pelo Git) e salva imagens em `media/`.

Outras rotas úteis: `/admin/` (painel do Django), `/status/` (diagnóstico de
banco) e `/healthz/` (checagem simples de disponibilidade).

## Variáveis de ambiente

Veja `.env.example`. Em produção elas ficam no painel do App Platform.

| Variável | Para quê |
| --- | --- |
| `DJANGO_SECRET_KEY` | Chave secreta (gere uma nova para produção) |
| `DJANGO_DEBUG` | `False` em produção |
| `DJANGO_ALLOWED_HOSTS` | Domínios permitidos, separados por vírgula |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Domínios com `https://`, separados por vírgula |
| `DATABASE_URL` | PostgreSQL; em branco usa SQLite |
| `SPACES_ACCESS_KEY_ID`, `SPACES_SECRET_ACCESS_KEY`, `SPACES_BUCKET_NAME`, `SPACES_REGION` | Spaces para as imagens; em branco usa `media/` local |
| `SPACES_CDN_DOMAIN`, `SPACES_URL_EXPIRE_SECONDS` | Opcionais (CDN e validade das URLs assinadas) |

## Publicando no DigitalOcean App Platform

Tudo isto é feito na **sua** conta do DigitalOcean (os custos são seus).
Pré-requisitos: uma conta, um banco PostgreSQL gerenciado e um Space
criados por você, na mesma região do app.

1. Faça um **fork** deste repositório para a sua conta/organização do
   GitHub. O App Platform publica a partir do **seu** fork, com deploy
   automático a cada push na branch `main`.
2. No painel: **Create → App Platform**, escolha o **seu** repositório e a
   branch `main`. Se preferir, use o `.do/app.yaml` (**Edit Your App Spec**):
   troque os placeholders `SEU_`/`TROQUE_` pelos seus valores.
3. **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   **Run Command**: `gunicorn config.wsgi:application --bind 0.0.0.0:8080`
4. Configure as variáveis de ambiente da tabela acima **no painel** (as
   sensíveis como *Encrypt*; nunca no Git — o `.env` é só local) e vincule o banco em **Add Resource → Database** (isso cria a
   `DATABASE_URL` e libera o app no firewall do banco).
5. Depois do primeiro deploy, no **Console** do componente web:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```
6. Em **Settings → Domains**, adicione o domínio (a DigitalOcean emite o
   HTTPS) e inclua-o em `DJANGO_ALLOWED_HOSTS` e `DJANGO_CSRF_TRUSTED_ORIGINS`.

A cada deploy com mudança de modelo, rode `python manage.py migrate` de novo
no Console.

## Estrutura

```
config/            # settings, urls, wsgi
core/              # login, painel, cronograma, perfil, colaboradores, troca de senha
questoes/          # disciplinas, frentes, assuntos, questões, planejamento, estatísticas
templates/         # core/ (layouts e telas gerais) e questoes/
static/vendor/     # Quill (editor) e KaTeX (fórmulas), servidos localmente
.do/app.yaml       # App Spec do App Platform
```

## Próximos passos

- Exportar as questões e os perfis para montar o material impresso.
- Tela própria para a coordenação cadastrar professores (hoje é pelo `/admin/`).
- Testes automatizados (os arquivos `tests.py` ainda estão vazios).
