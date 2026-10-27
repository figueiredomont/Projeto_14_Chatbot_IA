import json
import os
import time
import uuid
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

# Carrega as variáveis do arquivo .env
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")

MODELO = "openai/gpt-oss-120b"

# As conversas ficam salvas neste arquivo, ao lado do app.py
ARQUIVO = Path(__file__).parent / "conversas.json"

# Tons de azul usados nas faixas de cor das conversas
CORES = ["#3B6CCB", "#5B8DEF", "#6366F1", "#0EA5E9"]

# (título, descrição, mensagem enviada ao clicar)
CARTOES = [
    (
        "Explicar",
        "Um assunto difícil, em linguagem simples.",
        "Quero que você me explique um assunto difícil em linguagem simples. Pergunte qual é o assunto.",
    ),
    (
        "Escrever",
        "Um e-mail profissional, claro e educado.",
        "Quero escrever um e-mail profissional, claro e educado. Pergunte para quem é e qual é o objetivo.",
    ),
    (
        "Criar",
        "Ideias criativas para o seu projeto.",
        "Quero ideias criativas para um projeto. Pergunte qual é o projeto.",
    ),
    (
        "Programar",
        "Um conceito novo, com exemplos.",
        "Quero aprender um conceito de programação com exemplos. Pergunte qual conceito.",
    ),
]

st.set_page_config(
    page_title="Chatbot Groq",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------- Versão do Streamlit ----------
def _versao(texto: str) -> tuple:
    partes = []
    for p in texto.split(".")[:2]:
        digitos = "".join(c for c in p if c.isdigit())
        partes.append(int(digitos) if digitos else 0)
    return tuple(partes)


if _versao(st.__version__) < (1, 41):
    st.error(
        f"Seu Streamlit é o {st.__version__}, e este app precisa do 1.41 ou mais novo. "
        "Feche o app e rode: python -m pip install -U streamlit"
    )
    st.stop()

# ---------- Estilo ----------
# O estilo define as próprias cores e funciona com o tema claro ou escuro do Streamlit.
# Paleta: fundo (#EEF3FB), azul escuro (#1E3A8A), azul (#3B6CCB), azul claro (#5B8DEF),
#         linha (#D5E2F5), texto (#1F2A44), texto suave (#5B6B8C), resposta (#FFFDF8)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    .stApp, .stApp button, .stApp input, .stApp textarea {font-family: 'Inter', sans-serif;}

    /* Fundo e texto base */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background: linear-gradient(180deg, #F4F7FC 0%, #E3ECF9 100%);
        color: #1F2A44;
    }
    [data-testid="stHeader"] {background: transparent;}
    [data-testid="stHeader"] * {color: #5B6B8C;}
    #MainMenu, footer {visibility: hidden;}
    [data-testid="stAppDeployButton"], .stDeployButton {display: none;}
    .block-container {padding-top: 2rem; max-width: 960px;}

    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] strong,
    [data-testid="stMarkdownContainer"] em,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4,
    [data-testid="stMarkdownContainer"] td,
    [data-testid="stMarkdownContainer"] th {color: #1F2A44;}
    [data-testid="stMarkdownContainer"] a {color: #3B6CCB;}
    [data-testid="stMarkdownContainer"] code {background: #E3ECF9; color: #1E3A8A;}
    [data-testid="stCode"], [data-testid="stMarkdownContainer"] pre {background: #F1F5FB !important;}
    [data-testid="stCode"] *, [data-testid="stMarkdownContainer"] pre * {color: #1F2A44 !important;}

    /* Cabeçalho */
    .hero {
        position: relative;
        overflow: hidden;
        background: linear-gradient(135deg, #555555 0%, #777777 55%, #999999 100%);
        border-radius: 22px;
        padding: 1.6rem 1.9rem;
        margin-bottom: 1.4rem;
        box-shadow: 0 12px 30px rgba(30, 58, 138, 0.25);
        color: #FFFFFF;
    }
    .hero::after {
        content: "";
        position: absolute;
        right: -40px;
        top: -50px;
        width: 180px;
        height: 180px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.12);
    }
    .hero-t {font-size: 2.3rem; font-weight: 800; letter-spacing: -0.01em; line-height: 1.15; color: #FFFFFF;}
    .hero-s {margin-top: 0.35rem; font-size: 1.02rem; font-weight: 400; color: rgba(255, 255, 255, 0.92);}
    .status {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        margin-top: 1rem;
        padding: 0.3rem 0.85rem;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.15);
        font-size: 0.85rem;
        color: #FFFFFF;
    }
    .dot {width: 8px; height: 8px; border-radius: 50%; background: #7CF0B0;}

    /* Barra lateral */
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {background: #EAF1FB;}
    [data-testid="stSidebar"] {border-right: 1px solid #D5E2F5;}
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stExpandSidebarButton"],
    [data-testid="stSidebarCollapsedControl"] {visibility: visible !important;}
    [data-testid="stSidebarCollapseButton"] *,
    [data-testid="stExpandSidebarButton"] *,
    [data-testid="stSidebarCollapsedControl"] * {color: #3B6CCB !important;}

    .rotulo {color: #5B6B8C; font-size: 0.85rem; font-weight: 500; margin: 1.1rem 0 0.3rem 0;}
    .vazio {color: #5B6B8C; font-size: 0.92rem; font-weight: 400;}

    .stats {display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; margin-top: 1.4rem;}
    .stat {
        background: #FFFFFF;
        border: 1px solid #D5E2F5;
        border-top: 3px solid var(--cor, #3B6CCB);
        border-radius: 12px;
        padding: 0.6rem 0.8rem;
        box-shadow: 0 2px 8px rgba(30, 58, 138, 0.06);
    }
    .stat b {display: block; font-size: 1.6rem; font-weight: 700; color: var(--cor, #3B6CCB); line-height: 1.15;}
    .stat span {color: #5B6B8C; font-size: 0.85rem; font-weight: 400;}
    .modelo {margin-top: 0.8rem; color: #5B6B8C; font-size: 0.85rem; font-weight: 400;}
    .modelo b {display: block; font-size: 0.95rem; font-weight: 600; color: #1F2A44;}

    /* Cartões de sugestão */
    .st-key-card_0 {--cor: #3B6CCB;}
    .st-key-card_1 {--cor: #5B8DEF;}
    .st-key-card_2 {--cor: #6366F1;}
    .st-key-card_3 {--cor: #0EA5E9;}
    [class*="st-key-card_"] {
        background: #FFFFFF;
        border: 1px solid #D5E2F5;
        border-top: 3px solid var(--cor, #3B6CCB);
        border-radius: 16px;
        padding: 1.1rem 1.15rem;
        box-shadow: 0 4px 14px rgba(30, 58, 138, 0.07);
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    [class*="st-key-card_"]:hover {border-color: var(--cor, #3B6CCB); box-shadow: 0 8px 22px rgba(30, 58, 138, 0.14);}
    [class*="st-key-card_"] .stButton > button:hover {border-color: var(--cor); color: var(--cor);}
    .ct {font-size: 1.2rem; font-weight: 700; color: var(--cor, #3B6CCB); line-height: 1.2;}
    .cd {color: #5B6B8C; font-size: 0.95rem; font-weight: 400; line-height: 1.5;}

    /* Boas-vindas */
    .saudacao {font-size: 1.7rem; font-weight: 700; color: #1F2A44; margin: 0 0 0.3rem 0;}
    .info {display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.8rem; margin: 1rem 0 1.4rem 0;}
    @media (max-width: 900px) {.info {grid-template-columns: 1fr;}}
    .bloco {
        background: #FFFFFF;
        border: 1px solid #D5E2F5;
        border-top: 3px solid var(--cor, #3B6CCB);
        border-radius: 16px;
        padding: 1rem 1.1rem;
        box-shadow: 0 4px 14px rgba(30, 58, 138, 0.07);
    }
    .bt {font-size: 1.1rem; font-weight: 700; color: var(--cor, #3B6CCB); line-height: 1.2;}
    .bd {color: #5B6B8C; font-size: 0.92rem; font-weight: 400; line-height: 1.5; margin-top: 0.25rem;}

    /* Mensagens */
    [data-testid="stChatMessage"] {
        border-radius: 14px;
        padding: 0.9rem 1.1rem;
        margin: 0 0 1rem 0;
        box-shadow: 0 4px 14px rgba(30, 58, 138, 0.10);
    }
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li {font-size: 1.02rem; line-height: 1.65;}

    /* Respostas do assistente: balão claro com faixa azul */
    [data-testid="stChatMessage"] {
        background: #FFFDF8;
        border: 1px solid #E8E2D4;
        border-left: 4px solid #3B6CCB;
        color: #1F2A44;
    }
    [data-testid="stChatMessage"] [data-testid^="stChatMessageAvatar"] {
        background: #E3ECFB;
        border-radius: 10px;
    }

    /* Suas mensagens: barra azul */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]),
    [data-testid="stChatMessage"][aria-label="Chat message from user"] {
        background: linear-gradient(90deg, #3B6CCB 0%, #4C7FDB 100%);
        border: none;
        color: #FFFFFF;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stMarkdownContainer"],
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stMarkdownContainer"] p,
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stMarkdownContainer"] li,
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stMarkdownContainer"] strong,
    [data-testid="stChatMessage"][aria-label="Chat message from user"] [data-testid="stMarkdownContainer"],
    [data-testid="stChatMessage"][aria-label="Chat message from user"] [data-testid="stMarkdownContainer"] p {
        color: #FFFFFF;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid^="stChatMessageAvatar"],
    [data-testid="stChatMessage"][aria-label="Chat message from user"] [data-testid^="stChatMessageAvatar"] {
        background: rgba(255, 255, 255, 0.22);
    }
    [data-testid="stSpinner"], [data-testid="stSpinner"] * {color: #5B6B8C;}

    /* Campo de escrever (cores próprias, para o texto nunca ficar invisível) */
    [data-testid="stBottom"], [data-testid="stBottomBlockContainer"] {
        background: linear-gradient(to top, #E3ECF9 65%, rgba(227, 236, 249, 0));
    }
    [data-testid="stChatInput"] {
        background: #FFFFFF;
        border: 1px solid #D5E2F5;
        border-radius: 18px;
        box-shadow: 0 8px 24px rgba(30, 58, 138, 0.14);
    }
    [data-testid="stChatInput"] div {background: transparent; border-color: transparent !important;}
    [data-testid="stChatInput"]:focus-within {border-color: #3B6CCB; box-shadow: 0 8px 24px rgba(59, 108, 203, 0.25);}
    [data-testid="stChatInput"] div:focus-within {box-shadow: none !important; outline: none !important;}
    [data-testid="stChatInput"] textarea {
        background: transparent !important;
        color: #1F2A44 !important;
        -webkit-text-fill-color: #1F2A44;
        caret-color: #3B6CCB;
    }
    [data-testid="stChatInput"] textarea::placeholder {color: #7A8AA8; opacity: 1; -webkit-text-fill-color: #7A8AA8;}
    [data-testid="stChatInput"] button,
    [data-testid="stChatInputSubmitButton"] {
        background: #3B6CCB !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 12px !important;
    }
    [data-testid="stChatInput"] button:hover,
    [data-testid="stChatInputSubmitButton"]:hover {background: #2F5BC4 !important;}
    [data-testid="stChatInput"] button svg {fill: #FFFFFF; color: #FFFFFF;}

    /* Botões */
    .stButton > button {
        background: #FFFFFF;
        color: #1F2A44;
        border: 1px solid #D5E2F5;
        border-radius: 12px;
        min-height: 2.7rem;
        font-weight: 500;
        justify-content: flex-start;
        padding-left: 1.1rem;
        box-shadow: 0 2px 6px rgba(30, 58, 138, 0.06);
        transition: border-color 0.15s ease, background 0.15s ease;
    }
    .stButton > button p {
        color: inherit;
        text-align: left;
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .stButton > button > div {justify-content: flex-start; width: 100%;}
    .stButton > button:hover {border-color: #3B6CCB; background: #F3F7FE; color: #1F2A44;}
    .stButton > button:focus-visible {outline: 2px solid #3B6CCB; outline-offset: 2px;}

    /* Conversa aberta na lista */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {
        background: #DCE8FB;
        border-color: #3B6CCB;
        color: #1E3A8A;
    }

    /* Botão de nova conversa (destaque) */
    .st-key-nova button {
        background: linear-gradient(90deg, #3B6CCB 0%, #4C7FDB 100%);
        border: none;
        color: #FFFFFF;
        justify-content: center;
        padding-left: 0;
        box-shadow: 0 6px 16px rgba(59, 108, 203, 0.35);
    }
    .st-key-nova button > div {justify-content: center;}
    .st-key-nova button p {text-align: center; font-weight: 600; color: #FFFFFF;}
    .st-key-nova button:hover {background: linear-gradient(90deg, #2F5BC4 0%, #3B6CCB 100%); color: #FFFFFF;}

    /* Botões de apagar */
    [class*="st-key-del_"] button {
        justify-content: center;
        padding-left: 0;
        padding-right: 0;
        color: #5B6B8C;
    }
    [class*="st-key-del_"] button > div {justify-content: center;}
    [class*="st-key-del_"] button:hover {color: #C0392B; border-color: #C0392B;}

    /* Botões dos cartões */
    [class*="st-key-card_"] .stButton > button {justify-content: center; padding-left: 0;}
    [class*="st-key-card_"] .stButton > button > div {justify-content: center;}
    [class*="st-key-card_"] .stButton > button p {text-align: center;}
    </style>
    """,
    unsafe_allow_html=True,
)

if not API_KEY:
    st.error("GROQ_API_KEY não encontrada. Crie um arquivo .env com GROQ_API_KEY=sua_chave e reinicie o app.")
    st.stop()


# ---------- Conversas salvas ----------
def carregar_conversas() -> dict:
    try:
        return json.loads(ARQUIVO.read_text(encoding="utf-8"))
    except Exception:
        return {}


def salvar_conversas() -> None:
    try:
        ARQUIVO.write_text(
            json.dumps(st.session_state.conversas, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass


# Cria o client da Groq (uma vez por sessão)
if "client" not in st.session_state:
    st.session_state.client = Groq(api_key=API_KEY)

if "conversas" not in st.session_state:
    st.session_state.conversas = carregar_conversas()
    st.session_state.atual = None  # None = conversa nova, ainda sem mensagens

conversas = st.session_state.conversas
if st.session_state.atual not in conversas:
    st.session_state.atual = None

# ---------- Entrada do usuário ----------
# O campo fica fixo no rodapé; lê-se aqui para que a tela já nasça atualizada
pergunta = st.chat_input("Digite sua mensagem...")
if not pergunta and "pendente" in st.session_state:
    pergunta = st.session_state.pop("pendente")

responder = False
if pergunta:
    # Primeira mensagem: cria a conversa, com título tirado da pergunta
    if st.session_state.atual is None:
        novo_id = uuid.uuid4().hex[:8]
        titulo = " ".join(pergunta.split())
        titulo = titulo[:34] + ("…" if len(titulo) > 34 else "")
        conversas[novo_id] = {"titulo": titulo, "criada": time.time(), "mensagens": []}
        st.session_state.atual = novo_id
    conversas[st.session_state.atual]["mensagens"].append({"role": "user", "content": pergunta})
    responder = True

# ---------- Barra lateral ----------
with st.sidebar:
    if st.button("Nova conversa", use_container_width=True, key="nova"):
        st.session_state.atual = None
        st.rerun()

    st.markdown('<div class="rotulo">Suas conversas</div>', unsafe_allow_html=True)

    ordenadas = sorted(conversas.items(), key=lambda kv: kv[1].get("criada", 0), reverse=True)
    if ordenadas:
        # Cada conversa ganha uma faixa de cor na lateral do botão
        regras = "".join(
            f".st-key-abrir_{cid} .stButton > button "
            f"{{border-left: 4px solid {CORES[sum(ord(ch) for ch in cid) % len(CORES)]} !important;}}"
            for cid, _ in ordenadas
        )
        st.markdown(f"<style>{regras}</style>", unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="vazio">Suas conversas aparecem aqui depois da primeira mensagem.</div>',
            unsafe_allow_html=True,
        )

    for cid, conversa in ordenadas:
        c_abrir, c_apagar = st.columns([5, 1], gap="small")
        aberta = cid == st.session_state.atual
        if c_abrir.button(
            conversa["titulo"],
            key=f"abrir_{cid}",
            use_container_width=True,
            type="primary" if aberta else "secondary",
        ):
            st.session_state.atual = cid
            st.rerun()
        if c_apagar.button("×", key=f"del_{cid}", use_container_width=True, help="Apagar conversa"):
            del conversas[cid]
            if aberta:
                st.session_state.atual = None
            salvar_conversas()
            st.rerun()

    total_msgs = sum(len(c["mensagens"]) for c in conversas.values())
    st.markdown(
        f'<div class="stats">'
        f'<div class="stat" style="--cor:#3B6CCB"><b>{len(conversas)}</b><span>conversas</span></div>'
        f'<div class="stat" style="--cor:#0EA5E9"><b>{total_msgs}</b><span>mensagens</span></div>'
        f"</div>"
        f'<div class="modelo">Modelo<b>{MODELO}</b></div>',
        unsafe_allow_html=True,
    )

# ---------- Chat ----------
st.markdown(
    '<div class="hero">'
    '<div class="hero-t"> Chatbot Groq</div>'
    '<div class="hero-s">Pergunte qualquer coisa. Estou aqui para ajudar!</div>'
    '<div class="status"><span class="dot"></span>Online e pronto para conversar</div>'
    "</div>",
    unsafe_allow_html=True,
)

atual = st.session_state.atual
mensagens = conversas[atual]["mensagens"] if atual else []

# Tela de boas-vindas
if not mensagens:
    st.markdown('<div class="saudacao">Como posso ajudar hoje?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="info">'
        '<div class="bloco" style="--cor:#6366F1"><div class="bt">Memória</div>'
        '<div class="bd">Lembra do que foi dito durante a conversa.</div></div>'
        '<div class="bloco" style="--cor:#0EA5E9"><div class="bt">Conversas salvas</div>'
        '<div class="bd">Ficam guardadas neste computador e voltam quando você abrir o app.</div></div>'
        f'<div class="bloco" style="--cor:#3B6CCB"><div class="bt">Modelo</div><div class="bd">{MODELO}</div></div>'
        "</div>",
        unsafe_allow_html=True,
    )
    linhas = [st.columns(2, gap="medium"), st.columns(2, gap="medium")]
    for i, (titulo_c, descricao, envio) in enumerate(CARTOES):
        with linhas[i // 2][i % 2]:
            with st.container(key=f"card_{i}"):
                st.markdown(
                    f'<div class="ct">{titulo_c}</div><div class="cd">{descricao}</div>',
                    unsafe_allow_html=True,
                )
                if st.button("Perguntar", use_container_width=True, key=f"cartao_{i}"):
                    st.session_state.pendente = envio
                    st.rerun()

# Histórico
for msg in mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Resposta da Groq
if responder:
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                resposta = st.session_state.client.chat.completions.create(
                    model=MODELO,
                    messages=mensagens,
                )
                texto = resposta.choices[0].message.content
            except Exception as e:
                texto = None
                st.error(f"Não foi possível obter a resposta da Groq: {e}")

        if texto is not None:
            # Guarda a resposta e atualiza a barra lateral
            mensagens.append({"role": "assistant", "content": texto})
            salvar_conversas()
            st.rerun()
        else:
            # Remove a pergunta sem resposta para não quebrar o histórico
            mensagens.pop()
            if not mensagens:
                del conversas[st.session_state.atual]
                st.session_state.atual = None