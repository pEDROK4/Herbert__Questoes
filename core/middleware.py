from django.shortcuts import redirect
from django.urls import reverse


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
