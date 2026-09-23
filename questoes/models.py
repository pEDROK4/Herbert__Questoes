from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Disciplina(models.Model):
    """
    Ex: Matemática, Física, Química, Redação...
    """
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Disciplina"
        verbose_name_plural = "Disciplinas"

    def __str__(self):
        return self.nome


# Nomes exatos das disciplinas em que cada "frente" já é uma matéria
# independente (Sociologia/Filosofia e Português) — nelas o cursinho
# cobre só 15 aulas por matéria, contra 30 nas demais disciplinas.
NOMES_DISCIPLINAS_LIMITE_15_AULAS = {"Sociologia/Filosofia", "Português"}


class Frente(models.Model):
    """
    Cada disciplina é dividida em duas frentes (normalmente "Frente A" e
    "Frente B"). Na Sociologia/Filosofia, cada frente é a própria
    matéria (ex: Frente A = "Sociologia", Frente B = "Filosofia") — por
    isso o nome de exibição é livre, mas a letra continua identificando
    de forma fixa qual é a primeira e qual é a segunda frente.
    """

    class Letra(models.TextChoices):
        A = "A", "Frente A"
        B = "B", "Frente B"

    disciplina = models.ForeignKey(
        Disciplina, on_delete=models.CASCADE, related_name="frentes"
    )
    letra = models.CharField(max_length=1, choices=Letra.choices)
    nome = models.CharField(
        max_length=100,
        help_text='Nome exibido para a frente. Ex: "Frente A" ou, no caso '
        'de Sociologia/Filosofia, o nome da matéria em si ("Sociologia").',
    )
    professores = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="frentes_atribuidas",
        blank=True,
        verbose_name="Professores responsáveis",
        help_text="Só quem estiver aqui vê e cadastra conteúdo desta frente "
        "no painel. Coordenadores (superusuários) sempre veem todas.",
    )

    class Meta:
        ordering = ["disciplina__nome", "letra"]
        verbose_name = "Frente"
        verbose_name_plural = "Frentes"
        constraints = [
            models.UniqueConstraint(
                fields=["disciplina", "letra"], name="frente_unica_por_disciplina"
            )
        ]

    def __str__(self):
        return f"{self.disciplina} — {self.nome}"

    @property
    def limite_aula(self):
        """
        Quantas aulas essa frente cobre: 15 para Sociologia/Filosofia e
        Português (Gramática/Literatura), 30 para as demais disciplinas.
        """
        if self.disciplina.nome in NOMES_DISCIPLINAS_LIMITE_15_AULAS:
            return 15
        return 30


class Assunto(models.Model):
    """
    Um conteúdo dentro de uma frente. Ex: dentro de Matemática — Frente A,
    "Funções do 1º grau", "Trigonometria" etc. O mesmo nome de assunto
    pode existir em frentes diferentes, então a combinação frente + nome
    é que precisa ser única. A disciplina vem sempre através da frente.
    """

    AULA_CHOICES = [(i, f"Aula {i}") for i in range(1, 31)]

    frente = models.ForeignKey(
        Frente, on_delete=models.CASCADE, related_name="assuntos"
    )
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    aula = models.PositiveSmallIntegerField(
        choices=AULA_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        help_text="A qual aula (1 a 30) este conteúdo se refere.",
    )

    class Meta:
        ordering = ["frente__disciplina__nome", "frente__letra", "aula", "nome"]
        verbose_name = "Assunto"
        verbose_name_plural = "Assuntos"
        constraints = [
            models.UniqueConstraint(
                fields=["frente", "nome"], name="assunto_unico_por_frente"
            )
        ]

    def __str__(self):
        return f"{self.frente} — {self.nome}"

    @property
    def disciplina(self):
        return self.frente.disciplina


class Questao(models.Model):
    """
    Uma questão de múltipla escolha. O texto do enunciado é guardado
    como texto simples por enquanto — quando o editor de questões
    entrar, ele pode passar a guardar HTML/Markdown aqui sem precisar
    mudar o banco.
    """

    assunto = models.ForeignKey(
        Assunto,
        on_delete=models.PROTECT,
        related_name="questoes",
        help_text="O módulo/assunto ao qual esta questão pertence. A disciplina vem automaticamente dele.",
    )
    enunciado = models.TextField()

    # Origem da questão: ou veio de algum vestibular (banca/ano/prova
    # preenchidos) ou é de autoria do próprio professor (autoria_propria
    # marcado, e os três campos de vestibular ficam em branco).
    autoria_propria = models.BooleanField(default=False)
    banca = models.CharField(max_length=100, blank=True)
    ano = models.PositiveSmallIntegerField(null=True, blank=True)
    prova = models.CharField(
        max_length=150,
        blank=True,
        help_text='Nome/identificação da prova. Ex: "1ª fase", "2º dia".',
    )

    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="questoes_criadas",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Questão"
        verbose_name_plural = "Questões"

    def __str__(self):
        preview = self.enunciado.strip().replace("\n", " ")
        if len(preview) > 60:
            preview = preview[:57] + "..."
        return f"#{self.pk} — {preview}" if self.pk else preview

    @property
    def disciplina(self):
        """
        A matéria vem sempre através do módulo (assunto) — não existe
        mais um campo separado para isso, então não tem como as duas
        informações ficarem inconsistentes entre si.
        """
        return self.assunto.disciplina

    @property
    def tem_alternativa_correta(self):
        return self.alternativas.filter(correta=True).exists()


class Alternativa(models.Model):
    questao = models.ForeignKey(
        Questao, on_delete=models.CASCADE, related_name="alternativas"
    )
    letra = models.CharField(max_length=1)
    texto = models.TextField()
    correta = models.BooleanField(default=False)

    class Meta:
        ordering = ["letra"]
        verbose_name = "Alternativa"
        verbose_name_plural = "Alternativas"
        constraints = [
            models.UniqueConstraint(
                fields=["questao", "letra"], name="letra_unica_por_questao"
            )
        ]

    def __str__(self):
        return f"{self.letra}) {self.texto[:40]}"


def caminho_imagem_questao(instance, filename):
    # Organiza os uploads por questão, para não virar uma pasta única
    # gigante. Ex: questoes/imagens/42/grafico.png
    questao_id = instance.questao_id or "sem-questao"
    return f"questoes/imagens/{questao_id}/{filename}"


class ImagemQuestao(models.Model):
    """
    Usa o storage padrão do projeto (settings.STORAGES["default"]),
    que é o Spaces em produção e a pasta media/ local em desenvolvimento
    — não precisa de nenhuma lógica extra aqui para isso funcionar.
    """
    questao = models.ForeignKey(
        Questao, on_delete=models.CASCADE, related_name="imagens"
    )
    arquivo = models.ImageField(upload_to=caminho_imagem_questao)
    legenda = models.CharField(max_length=255, blank=True)
    enviado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["enviado_em"]
        verbose_name = "Imagem da questão"
        verbose_name_plural = "Imagens da questão"

    def __str__(self):
        return self.legenda or self.arquivo.name
