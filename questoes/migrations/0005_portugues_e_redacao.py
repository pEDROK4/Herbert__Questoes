# Adiciona as disciplinas de Português (frentes Gramática e Literatura,
# cada uma com limite de 15 aulas — mesmo esquema de Sociologia/Filosofia)
# e Redação (uma frente só, "Redação", com o limite padrão de 30 aulas).

from django.db import migrations


def semear_portugues_e_redacao(apps, schema_editor):
    Disciplina = apps.get_model("questoes", "Disciplina")
    Frente = apps.get_model("questoes", "Frente")

    portugues, _ = Disciplina.objects.get_or_create(nome="Português")
    Frente.objects.get_or_create(
        disciplina=portugues, letra="A", defaults={"nome": "Gramática"}
    )
    Frente.objects.get_or_create(
        disciplina=portugues, letra="B", defaults={"nome": "Literatura"}
    )

    redacao, _ = Disciplina.objects.get_or_create(nome="Redação")
    Frente.objects.get_or_create(
        disciplina=redacao, letra="A", defaults={"nome": "Redação"}
    )


def remover_portugues_e_redacao(apps, schema_editor):
    Disciplina = apps.get_model("questoes", "Disciplina")
    Disciplina.objects.filter(nome__in=["Português", "Redação"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("questoes", "0004_questao_autoria_propria_questao_prova"),
    ]

    operations = [
        migrations.RunPython(
            semear_portugues_e_redacao, reverse_code=remover_portugues_e_redacao
        ),
    ]
