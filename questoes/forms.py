from django import forms

from .models import Alternativa, Assunto, Frente, Questao
from .sanitizacao import enunciado_esta_vazio, sanitizar_html_enunciado


class SelectComLimiteAula(forms.Select):
    """
    Select de frente que carrega, em cada <option>, o limite de aulas
    daquela frente (15 para Sociologia/Filosofia, 30 para as demais) —
    o JS do modal de cadastro usa esse atributo para restringir as
    opções do campo "aula" na hora, sem round-trip ao servidor.
    """

    def __init__(self, *args, limites=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.limites = limites or {}

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        limite = self.limites.get(str(value))
        if limite:
            option["attrs"]["data-limite-aula"] = limite
        return option


class AssuntoForm(forms.ModelForm):
    """
    Formulário de cadastro de um novo conteúdo (assunto). O campo
    "frente" já identifica a disciplina — cada opção do dropdown é
    agrupada visualmente por disciplina (optgroup), então escolher a
    frente também escolhe a disciplina, sem precisar de um segundo
    campo dependente.

    O dropdown só lista as frentes que o professor logado pode usar —
    isso também vale como validação no backend: se alguém tentar
    forjar o POST com o pk de uma frente que não é dele, o
    ModelChoiceField rejeita, porque o valor não está no queryset
    permitido (veja `usuario` no __init__).
    """

    frente = forms.ModelChoiceField(
        queryset=Frente.objects.none(),
        label="Disciplina / frente",
    )

    class Meta:
        model = Assunto
        fields = ["frente", "nome", "descricao", "aula"]
        labels = {
            "nome": "Nome do assunto",
            "descricao": "Descrição do assunto",
            "aula": "Aula",
        }
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)

        queryset = Frente.objects.select_related("disciplina")
        if usuario is not None and not usuario.is_superuser:
            queryset = queryset.filter(professores=usuario)
        self.fields["frente"].queryset = queryset

        # Troca o widget pelo que carrega o limite de aula por opção,
        # antes de montar os <optgroup> — o setter de `choices` abaixo
        # também propaga a lista pro widget atual.
        limites = {str(frente.pk): frente.limite_aula for frente in queryset}
        self.fields["frente"].widget = SelectComLimiteAula(limites=limites)

        # Monta os <optgroup> por disciplina na mão, já que o
        # ModelChoiceField sozinho não agrupa.
        agrupado = {}
        for frente in queryset:
            agrupado.setdefault(frente.disciplina.nome, []).append(
                (frente.pk, frente.nome)
            )
        self.fields["frente"].choices = [
            (disciplina, opcoes) for disciplina, opcoes in agrupado.items()
        ]

    def clean(self):
        dados = super().clean()
        frente = dados.get("frente")
        aula = dados.get("aula")
        if frente is not None and aula is not None and aula > frente.limite_aula:
            self.add_error(
                "aula",
                f"{frente.disciplina.nome} só vai até a aula {frente.limite_aula}.",
            )
        return dados


LETRAS_ALTERNATIVAS = ["a", "b", "c", "d", "e"]


class QuestaoForm(forms.ModelForm):
    """
    Formulário de cadastro de questão. Junta num só form: a escolha do
    assunto (restrita ao que o professor pode usar, igual ao
    AssuntoForm), o enunciado rico (vem do editor Quill como HTML
    escondido num campo hidden, sanitizado em clean_enunciado), a
    origem (vestibular ou autoria própria) e até 5 alternativas com
    rádio marcando a correta — em vez de um formset, que exigiria
    gerenciar management form e não dá pra impor "só uma marcada como
    certa" com naturalidade.
    """

    assunto = forms.ModelChoiceField(
        queryset=Assunto.objects.none(),
        label="Assunto",
    )
    enunciado = forms.CharField(widget=forms.HiddenInput(), required=True)

    alternativa_a = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2}), label="Alternativa A"
    )
    alternativa_b = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2}), label="Alternativa B"
    )
    alternativa_c = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2}), label="Alternativa C", required=False
    )
    alternativa_d = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2}), label="Alternativa D", required=False
    )
    alternativa_e = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2}), label="Alternativa E", required=False
    )
    correta = forms.ChoiceField(
        choices=[("a", "A"), ("b", "B"), ("c", "C"), ("d", "D"), ("e", "E")],
        widget=forms.RadioSelect,
        label="Qual é a alternativa correta",
    )

    class Meta:
        model = Questao
        fields = [
            "assunto",
            "enunciado",
            "autoria_propria",
            "banca",
            "ano",
            "prova",
        ]
        labels = {
            "autoria_propria": "Questão de autoria própria (não é de vestibular)",
            "banca": "Banca",
            "ano": "Ano",
            "prova": "Prova",
        }
        widgets = {
            "autoria_propria": forms.CheckboxInput(),
            "ano": forms.NumberInput(attrs={"min": 1990, "max": 2100}),
        }

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["autoria_propria"].required = False

        queryset = Assunto.objects.select_related(
            "frente", "frente__disciplina"
        ).order_by("frente__disciplina__nome", "frente__letra", "aula", "nome")
        if usuario is not None and not usuario.is_superuser:
            queryset = queryset.filter(frente__professores=usuario)
        self.fields["assunto"].queryset = queryset

        # Optgroup por "Disciplina — Frente", pra ficar claro de qual
        # frente é cada assunto quando o professor tem mais de uma.
        agrupado = {}
        for assunto in queryset:
            rotulo_grupo = f"{assunto.frente.disciplina.nome} — {assunto.frente.nome}"
            agrupado.setdefault(rotulo_grupo, []).append(
                (assunto.pk, f"Aula {assunto.aula} — {assunto.nome}")
            )
        self.fields["assunto"].choices = [
            (grupo, opcoes) for grupo, opcoes in agrupado.items()
        ]

    def clean_enunciado(self):
        html_limpo = sanitizar_html_enunciado(self.cleaned_data.get("enunciado", ""))
        if enunciado_esta_vazio(html_limpo):
            raise forms.ValidationError("Escreva o enunciado da questão.")
        return html_limpo

    def clean(self):
        dados = super().clean()

        preenchidas = {}
        for letra in LETRAS_ALTERNATIVAS:
            texto = (dados.get(f"alternativa_{letra}") or "").strip()
            if texto:
                preenchidas[letra] = texto

        if len(preenchidas) < 2:
            self.add_error(None, "Cadastre pelo menos duas alternativas.")

        correta = dados.get("correta")
        if correta and preenchidas and correta not in preenchidas:
            self.add_error(
                "correta", "A alternativa marcada como correta precisa estar preenchida."
            )

        if dados.get("autoria_propria"):
            dados["banca"] = ""
            dados["ano"] = None
            dados["prova"] = ""

        self._alternativas_preenchidas = preenchidas
        return dados

    def save(self, commit=True, autor=None):
        questao = super().save(commit=False)
        if autor is not None:
            questao.autor = autor
        if commit:
            questao.save()
            self._salvar_alternativas(questao)
        return questao

    def _salvar_alternativas(self, questao):
        correta = self.cleaned_data["correta"]
        Alternativa.objects.bulk_create(
            Alternativa(
                questao=questao,
                letra=letra.upper(),
                texto=texto,
                correta=(letra == correta),
            )
            for letra, texto in self._alternativas_preenchidas.items()
        )
