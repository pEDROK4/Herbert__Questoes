from django.conf import settings
from django.db import DatabaseError
from django.shortcuts import redirect, render
from django.urls import reverse

from .models import ConfiguracaoSistema


def manutencao_ativa():
    """
    Manutenção ligada pelo botão da tela Configurações (banco) ou forçada
    pela variável de ambiente MODO_MANUTENCAO. Se o banco não responder ou
    a tabela ainda não existir (ex: antes do primeiro `migrate`), considera
    desligada em vez de derrubar o site inteiro com erro 500.
    """
    if settings.MODO_MANUTENCAO:
        return True
    try:
        return ConfiguracaoSistema.objects.filter(pk=1, manutencao_ativa=True).exists()
    except DatabaseError:
        return False


class ManutencaoMiddleware:
    """
    Com a manutenção ligada, todo mundo vê a página de manutenção (HTTP
    503) — exceto superusuários (coordenação), que continuam usando o site
    normalmente pra repopular/ajustar dados. Ficam sempre liberados: a
    tela de login e o logout (pra coordenação conseguir entrar), a raiz "/"
    e /healthz/ (a checagem de saúde da plataforma precisa continuar
    passando, senão o deploy é revertido), /status/, /admin/ e os arquivos
    estáticos/media.
    """

    PREFIXOS_LIBERADOS = ("/static/", "/media/", "/admin/", "/healthz/", "/status/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        caminho = request.path
        liberados = {"/", reverse("core:login"), reverse("core:logout")}
        if (
            caminho not in liberados
            and not caminho.startswith(self.PREFIXOS_LIBERADOS)
            and not request.user.is_superuser
            and manutencao_ativa()
        ):
            resposta = render(request, "core/manutencao.html", status=503)
            resposta["Retry-After"] = "3600"
            return resposta
        return self.get_response(request)


class ForcarTrocaSenhaMiddleware:
    """
    Se a pessoa logada ainda está com a senha genérica (perfil.senha_provisoria
    = True), trava qualquer página e manda direto pra troca de senha —
    só libera a própria página de troca, o logout e os arquivos
    estáticos/media. Fica assim até ela cadastrar uma senha nova.
    """

    CAMINHOS_LIBERADOS = {"core:trocar_senha", "core:logout"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario = request.user
        if usuario.is_authenticated:
            perfil = getattr(usuario, "perfil", None)
            if perfil and perfil.senha_provisoria:
                caminho_atual = request.path
                caminhos_liberados = {reverse(nome) for nome in self.CAMINHOS_LIBERADOS}
                bloqueado = (
                    caminho_atual not in caminhos_liberados
                    and not caminho_atual.startswith("/static/")
                    and not caminho_atual.startswith("/media/")
                    and not caminho_atual.startswith("/admin/")
                )
                if bloqueado:
                    return redirect("core:trocar_senha")
        return self.get_response(request)
