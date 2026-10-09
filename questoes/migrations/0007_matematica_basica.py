# Adiciona a disciplina "Matemática Básica" — um curso à parte da Matemática,
# com uma frente única (também chamada "Matemática Básica") e o limite
# padrão de 30 aulas. Mesmo esquema da Redação.

from django.db import migrations


def criar_matematica_basica(apps, schema_editor):
    Disciplina = apps.get_model("questoes", "Disciplina")
    Frente = apps.get_model("questoes", "Frente")

    disciplina, _ = Disciplina.objects.get_or_create(nome="Matemática Básica")
    Frente.objects.get_or_create(
        disciplina=disciplina, letra="A", defaults={"nome": "Matemática Básica"}
    )


def remover_matematica_basica(apps, schema_editor):
    # Só remove se ainda estiver vazia, pra nunca apagar aulas já cadastradas.
    Disciplina = apps.get_model("questoes", "Disciplina")
    Disciplina.objects.filter(
        nome="Matemática Básica", frentes__assuntos__isnull=True
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("questoes", "0006_remove_questao_dificuldade_remove_questao_status"),
    ]

    operations = [
        migrations.RunPython(criar_matematica_basica, reverse_code=remover_matematica_basica),
    ]
