from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import render


def home(request):
    """
    Página inicial. Só existe para provar que o deploy está funcionando
    de ponta a ponta — servidor, banco e arquivos estáticos. As telas
    reais (cronograma, questões, editor) entram aqui depois.
    """
    db_ok = None
    db_error = None
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        db_ok = True
    except Exception as exc:  # noqa: BLE001 - queremos mostrar qualquer erro
        db_ok = False
        db_error = str(exc)

    context = {
        "db_ok": db_ok,
        "db_error": db_error,
        "db_engine": connection.settings_dict.get("ENGINE", ""),
    }
    return render(request, "core/home.html", context)


def healthz(request):
    """
    Rota simples de 'saúde' do app, sem depender do banco. Útil para
    checagens automáticas de disponibilidade (o App Platform já faz a
    dele sozinho, mas é comum ter uma rota assim para monitoramento
    externo no futuro).
    """
    return HttpResponse("ok", content_type="text/plain")


@login_required
def painel(request):
    """
    Área logada dos professores. Por enquanto é só um placeholder — é
    aqui que depois entram o cronograma, a lista de questões e o editor.
    """
    return render(request, "core/painel.html", {"user": request.user})
