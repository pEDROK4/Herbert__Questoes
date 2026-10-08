from unittest import mock

from django.contrib.auth import get_user_model
from django.db import OperationalError
from django.test import TestCase, override_settings

from questoes.models import Frente

from .models import ConfiguracaoSistema

Usuario = get_user_model()


@override_settings(MODO_MANUTENCAO=True)
class ModoManutencaoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.prof = Usuario.objects.create_user("prof", password="x")
        cls.coord = Usuario.objects.create_superuser("coord", password="x")

    def test_visitante_ve_pagina_de_manutencao(self):
        resposta = self.client.get("/painel/")
        self.assertEqual(resposta.status_code, 503)
        self.assertContains(resposta, "Estamos em manutenção", status_code=503)
        self.assertEqual(resposta["Retry-After"], "3600")

    def test_professor_logado_ve_manutencao(self):
        self.client.force_login(self.prof)
        self.assertEqual(self.client.get("/painel/").status_code, 503)
        self.assertEqual(self.client.get("/painel/planejamento/").status_code, 503)

    def test_coordenacao_continua_usando_o_site(self):
        self.client.force_login(self.coord)
        self.assertEqual(self.client.get("/painel/").status_code, 200)

    def test_login_continua_acessivel_para_a_coordenacao_entrar(self):
        self.assertEqual(self.client.get("/login/").status_code, 200)
        resposta = self.client.post("/login/", {"username": "coord", "password": "x"})
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(self.client.get("/painel/").status_code, 200)

    def test_rotas_de_saude_ficam_liberadas(self):
        self.assertEqual(self.client.get("/healthz/").status_code, 200)
        self.assertEqual(self.client.get("/").status_code, 302)


@override_settings(MODO_MANUTENCAO=False)
class SemManutencaoTests(TestCase):
    def test_site_normal_quando_desligado(self):
        prof = Usuario.objects.create_user("prof", password="x")
        self.client.force_login(prof)
        self.assertEqual(self.client.get("/painel/").status_code, 200)


class ConfiguracoesTests(TestCase):
    """Tela Configurações: botão de manutenção e frentes dos professores."""

    @classmethod
    def setUpTestData(cls):
        cls.prof = Usuario.objects.create_user("prof", password="x")
        cls.coord = Usuario.objects.create_superuser("coord", password="x")
        cls.url = "/painel/configuracoes/"

    def test_so_a_coordenacao_acessa(self):
        self.client.force_login(self.prof)
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta["Location"].startswith("/painel/"))
        self.assertNotContains(self.client.get("/painel/"), "Modo de manutenção")

    def test_item_do_menu_so_para_coordenacao(self):
        self.client.force_login(self.prof)
        self.assertNotContains(self.client.get("/painel/"), "Configurações")
        self.client.force_login(self.coord)
        self.assertContains(self.client.get("/painel/"), "Configurações")

    def test_endereco_antigo_redireciona(self):
        self.client.force_login(self.coord)
        resposta = self.client.get("/painel/professores/")
        self.assertRedirects(resposta, self.url, fetch_redirect_response=False)

    def test_ligar_e_desligar_manutencao_pelo_botao(self):
        self.client.force_login(self.coord)
        self.client.post(self.url, {"acao": "manutencao", "ligar": "1"})
        self.assertTrue(ConfiguracaoSistema.carregar().manutencao_ativa)

        # Professor passa a ver a manutenção; coordenação segue normal.
        professor = self.client_class()
        professor.force_login(self.prof)
        self.assertEqual(professor.get("/painel/").status_code, 503)
        self.assertEqual(self.client.get("/painel/").status_code, 200)

        self.client.post(self.url, {"acao": "manutencao", "ligar": "0"})
        self.assertFalse(ConfiguracaoSistema.carregar().manutencao_ativa)
        self.assertEqual(professor.get("/painel/").status_code, 200)

    def test_professor_nao_consegue_ligar_a_manutencao(self):
        self.client.force_login(self.prof)
        self.client.post(self.url, {"acao": "manutencao", "ligar": "1"})
        self.assertFalse(ConfiguracaoSistema.carregar().manutencao_ativa)

    def test_atribuir_frentes_a_um_professor(self):
        frente = Frente.objects.get(disciplina__nome="Biologia", letra="A")
        self.client.force_login(self.coord)
        self.client.post(self.url, {"professor_id": self.prof.pk, "frentes": [frente.pk]})
        self.assertEqual(list(self.prof.frentes_atribuidas.all()), [frente])

        self.client.post(self.url, {"professor_id": self.prof.pk})
        self.assertEqual(self.prof.frentes_atribuidas.count(), 0)

    def test_manutencao_forcada_pela_variavel_aparece_na_tela(self):
        self.client.force_login(self.coord)
        with override_settings(MODO_MANUTENCAO=True):
            self.assertContains(self.client.get(self.url), "forçada")

    def test_site_nao_cai_se_a_tabela_de_configuracao_nao_existir(self):
        self.client.force_login(self.prof)
        with mock.patch.object(
            ConfiguracaoSistema.objects, "filter", side_effect=OperationalError("sem tabela")
        ):
            self.assertEqual(self.client.get("/painel/").status_code, 200)
