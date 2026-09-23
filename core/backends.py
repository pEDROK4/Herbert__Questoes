import re

from django.contrib.auth.backends import ModelBackend

from .models import PerfilProfessor


class TelefoneBackend(ModelBackend):
    """
    Autentica pelo telefone cadastrado em PerfilProfessor.telefone, em
    vez do username — usado pelos professores, que entram com o
    próprio celular. Funciona em paralelo ao ModelBackend padrão (login
    por usuário continua funcionando, é o que a coordenação usa).
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        telefone = re.sub(r"\D", "", username)
        if not telefone:
            return None

        try:
            perfil = PerfilProfessor.objects.select_related("usuario").get(
                telefone=telefone
            )
        except PerfilProfessor.DoesNotExist:
            return None

        usuario = perfil.usuario
        if usuario.check_password(password) and self.user_can_authenticate(usuario):
            return usuario
        return None
