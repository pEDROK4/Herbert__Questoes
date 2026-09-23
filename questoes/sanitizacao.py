"""
Limpeza do HTML que vem do editor de texto rico (Quill) antes de gravar
no banco. Existe pra duas coisas:

1) Segurança: um professor pode colar conteúdo de outro site (Word,
   Google Docs, uma página qualquer) — o clipboard pode trazer HTML
   com tags/atributos que a gente não quer guardar (nada de <script>,
   atributos "on*", estilos esquisitos etc).
2) Fórmulas (LaTeX/KaTeX): o Quill guarda a fórmula como
   `<span class="ql-formula" data-value="LATEX">...miolo renderizado
   pelo KaTeX...</span>`. O miolo é só a apresentação (um monte de
   <span> e tags <math> aninhadas) — não faz sentido gravar isso no
   banco, então a gente guarda só o `data-value` (o LaTeX em si) e
   deixa o miolo vazio; quem for exibir a questão depois re-renderiza
   a fórmula a partir do data-value com o KaTeX na hora.
"""

import bleach
from bs4 import BeautifulSoup

TAGS_PERMITIDAS = [
    "p", "br", "strong", "em", "u", "s",
    "ol", "ul", "li",
    "blockquote",
    "span", "img", "a",
]

ATRIBUTOS_PERMITIDOS = {
    "span": ["class", "data-value"],
    "img": ["src", "alt"],
    "a": ["href", "target", "rel"],
}

PROTOCOLOS_PERMITIDOS = ["http", "https", "data"]


def sanitizar_html_enunciado(html):
    if not html:
        return ""

    sopa = BeautifulSoup(html, "html.parser")
    for formula in sopa.select("span.ql-formula"):
        formula.clear()

    return bleach.clean(
        str(sopa),
        tags=TAGS_PERMITIDAS,
        attributes=ATRIBUTOS_PERMITIDOS,
        protocols=PROTOCOLOS_PERMITIDOS,
        strip=True,
    )


def enunciado_esta_vazio(html):
    """
    O Quill representa um editor "vazio" como "<p><br></p>" — isso não
    conta como conteúdo de verdade. Uma questão só com imagem ou só
    com fórmula (sem texto) conta como preenchida.
    """
    if not html:
        return True
    sopa = BeautifulSoup(html, "html.parser")
    tem_texto = bool(sopa.get_text(strip=True))
    tem_imagem = sopa.find("img") is not None
    tem_formula = sopa.find("span", class_="ql-formula") is not None
    return not (tem_texto or tem_imagem or tem_formula)
