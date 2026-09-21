# Banco de Questões — Cursinho

Projeto Django mínimo, já preparado para rodar local (SQLite) e em
produção no **DigitalOcean App Platform**, com **PostgreSQL** (Managed
Database) e **Spaces** (upload de imagens das questões). Ainda não tem
as telas de cronograma/questões/editor — o objetivo deste primeiro
esqueleto é validar a infraestrutura (deploy, banco, domínio, HTTPS)
antes de construir o resto.

## Rodando localmente

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # e ajuste se quiser

python manage.py migrate
python manage.py createsuperuser # crie seu usuário de professor/admin
python manage.py runserver
```

Abra http://127.0.0.1:8000 — a página inicial mostra se a conexão com
o banco está OK. Sem nada configurado no `.env`, o projeto usa SQLite
(arquivo `db.sqlite3`, já ignorado pelo Git) e salva uploads futuros em
`media/` local.

O painel de administração do Django (útil para cadastrar e revisar
dados enquanto as telas próprias não existem) fica em `/admin/`.

## Publicando no DigitalOcean App Platform

Pré-requisitos: banco PostgreSQL gerenciado e Space já criados (veja o
restante da conversa para os passos de cada um).

1. Suba este projeto para um repositório no GitHub (privado).
2. No painel da DigitalOcean: **Create → App Platform**, escolha o
   GitHub, o repositório e a branch `main`, com autodeploy ligado.
3. A plataforma detecta Python automaticamente. Ajuste o **Run
   Command** para:
   ```
   gunicorn config.wsgi:application --bind 0.0.0.0:8080
   ```
   E, se quiser coletar os arquivos estáticos no build, use como
   **Build Command**:
   ```
   pip install -r requirements.txt && python manage.py collectstatic --noinput
   ```
4. Escolha a **mesma região** do banco e do Space.
5. Em **Environment Variables**, adicione (marcando como *Encrypt* as
   sensíveis):
   - `DJANGO_SECRET_KEY` — gere uma nova, nunca reaproveite a de
     desenvolvimento (dá para gerar com
     `python -c "import secrets; print(secrets.token_urlsafe(50))"`)
   - `DJANGO_DEBUG` = `False`
   - `DJANGO_ALLOWED_HOSTS` = `${APP_DOMAIN}` (e depois inclua seu
     domínio próprio, quando configurar)
   - `DJANGO_CSRF_TRUSTED_ORIGINS` = `https://${APP_DOMAIN}` (idem)
   - `SPACES_ACCESS_KEY_ID`, `SPACES_SECRET_ACCESS_KEY`,
     `SPACES_BUCKET_NAME`, `SPACES_REGION` — do Space que você criou
6. Em **Add Resource → Database**, vincule o banco gerenciado já
   existente. Isso libera o app como fonte confiável no firewall do
   banco e cria a variável `DATABASE_URL` automaticamente — aponte a
   variável de ambiente `DATABASE_URL` do app para
   `${nome_do_banco.DATABASE_URL}`.
7. Clique em **Create App** e acompanhe os *Build Logs*.
8. Depois do primeiro deploy, abra o **Console** do app (aba
   *Console*, no componente web) e rode:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```
9. Em **Settings → Domains**, adicione seu domínio/subdomínio. A
   DigitalOcean mostra o registro DNS (normalmente um CNAME) para
   criar onde o domínio está registrado, e emite o certificado HTTPS
   automaticamente. Depois disso, atualize `DJANGO_ALLOWED_HOSTS` e
   `DJANGO_CSRF_TRUSTED_ORIGINS` para incluir o domínio final.

Existe também um `.do/app.yaml` neste projeto — é uma forma opcional
de descrever essa mesma configuração como arquivo (App Spec), caso
você prefira versionar isso junto com o código em vez de configurar
tudo pelo painel.

## Estrutura

```
config/          # configurações do projeto (settings, urls, wsgi)
core/             # app inicial: página de início, login, painel logado
templates/core/   # templates HTML
static/           # CSS/JS do projeto (vazio por enquanto)
.do/app.yaml      # App Spec opcional do App Platform
```

## Próximos passos

- Modelos de `Disciplina`, `Assunto`, `Questao`, `Alternativa`,
  `Imagem` e histórico de revisão.
- Grupos de permissão (professor, coordenador, revisor).
- Editor de questões com texto rico, imagens e fórmulas (LaTeX via
  KaTeX/MathJax).
- Lista, busca e filtros de questões.
- Cronograma das disciplinas.
