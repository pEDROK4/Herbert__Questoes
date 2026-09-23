from django.contrib import admin
from django.utils.html import format_html

from .models import Alternativa, Assunto, Disciplina, Frente, ImagemQuestao, Questao


@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ["nome", "total_frentes", "total_assuntos", "total_questoes"]
    search_fields = ["nome"]

    @admin.display(description="Frentes")
    def total_frentes(self, obj):
        return obj.frentes.count()

    @admin.display(description="Assuntos")
    def total_assuntos(self, obj):
        return Assunto.objects.filter(frente__disciplina=obj).count()

    @admin.display(description="Questões")
    def total_questoes(self, obj):
        # Disciplina não tem mais ligação direta com Questao — a
        # contagem passa sempre pela frente e pelo módulo (assunto) dela.
        return Questao.objects.filter(assunto__frente__disciplina=obj).count()


@admin.register(Frente)
class FrenteAdmin(admin.ModelAdmin):
    list_display = ["disciplina", "letra", "nome", "total_assuntos", "total_professores"]
    list_filter = ["disciplina"]
    search_fields = ["nome"]
    autocomplete_fields = ["disciplina"]
    filter_horizontal = ["professores"]

    @admin.display(description="Professores")
    def total_professores(self, obj):
        return obj.professores.count()

    @admin.display(description="Assuntos")
    def total_assuntos(self, obj):
        return obj.assuntos.count()


@admin.register(Assunto)
class AssuntoAdmin(admin.ModelAdmin):
    list_display = ["nome", "disciplina", "frente", "aula", "total_questoes"]
    list_filter = ["frente__disciplina", "frente", "aula"]
    search_fields = ["nome", "descricao"]
    autocomplete_fields = ["frente"]

    @admin.display(description="Disciplina", ordering="frente__disciplina")
    def disciplina(self, obj):
        return obj.frente.disciplina

    @admin.display(description="Questões")
    def total_questoes(self, obj):
        return obj.questoes.count()


class AlternativaInline(admin.TabularInline):
    model = Alternativa
    extra = 4
    max_num = 6
    fields = ["letra", "texto", "correta"]


class ImagemQuestaoInline(admin.TabularInline):
    model = ImagemQuestao
    extra = 1
    fields = ["arquivo", "legenda", "preview"]
    readonly_fields = ["preview"]

    @admin.display(description="Pré-visualização")
    def preview(self, obj):
        if obj.pk and obj.arquivo:
            return format_html(
                '<img src="{}" style="max-height: 80px;" />', obj.arquivo.url
            )
        return "—"


@admin.register(Questao)
class QuestaoAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "resumo_enunciado",
        "disciplina",
        "assunto",
        "autor",
        "tem_alternativa_correta",
        "criado_em",
    ]
    list_filter = ["assunto__frente__disciplina", "assunto"]
    search_fields = ["enunciado", "banca"]
    autocomplete_fields = ["assunto"]
    readonly_fields = ["autor", "criado_em", "atualizado_em"]
    inlines = [AlternativaInline, ImagemQuestaoInline]
    list_per_page = 25

    fieldsets = (
        (None, {"fields": ("assunto", "enunciado")}),
        ("Classificação", {"fields": ("banca", "ano")}),
        ("Controle", {"fields": ("autor", "criado_em", "atualizado_em")}),
    )

    @admin.display(description="Enunciado")
    def resumo_enunciado(self, obj):
        texto = obj.enunciado.strip().replace("\n", " ")
        return texto[:70] + ("..." if len(texto) > 70 else "")

    @admin.display(description="Disciplina", ordering="assunto__frente__disciplina")
    def disciplina(self, obj):
        return obj.assunto.disciplina

    @admin.display(description="Tem alternativa correta?", boolean=True)
    def tem_alternativa_correta(self, obj):
        return obj.tem_alternativa_correta

    def save_model(self, request, obj, form, change):
        # Preenche o autor automaticamente com quem está logado, na
        # primeira vez que a questão é salva.
        if not change or not obj.autor_id:
            obj.autor = request.user
        super().save_model(request, obj, form, change)
