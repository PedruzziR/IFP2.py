import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import gspread
from google.oauth2.service_account import Credentials
import datetime

# ================= BLOCO 1: DEFINIÇÃO DA MARCA D'ÁGUA =================
def inject_watermark(nome_paciente, id_sessao):
    watermark_style = f"""
    <style>
    .watermark {{
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        z-index: 9999;
        pointer-events: none;
        display: flex;
        flex-wrap: wrap;
        justify-content: space-around;
        align-content: space-around;
        opacity: 0.12;
        user-select: none;
    }}
    .watermark-text {{
        transform: rotate(-45deg);
        font-size: 22px;
        font-weight: bold;
        color: grey;
        white-space: nowrap;
        text-align: center;
        margin: 40px;
    }}
    </style>
    <div class="watermark">
        {"<div class='watermark-text'>INSTRUMENTO SIGILOSO<br>{paciente}<br>{sessao}</div>" * 20}
    </div>
    """.format(paciente=nome_paciente if nome_paciente else "PACIENTE NÃO IDENTIFICADO", sessao=id_sessao)
    
    st.markdown(watermark_style, unsafe_allow_html=True)

# ================= CONFIGURAÇÕES DE E-MAIL =================
SEU_EMAIL = st.secrets["EMAIL_USUARIO"]
SENHA_DO_EMAIL = st.secrets["SENHA_USUARIO"]

# ================= CONEXÃO COM GOOGLE SHEETS =================
@st.cache_resource
def conectar_planilha():
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS_JSON"])
    escopos = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=escopos)
    client = gspread.authorize(creds)
    return client.open("Controle_Tokens").sheet1 

try:
    planilha = conectar_planilha()
except Exception as e:
    st.error(f"Erro de conexão com o Banco de Dados: {e}")
    st.stop()

def enviar_email_resultados(nome, token, sexo, resultados_processados):
    assunto = f"Resultados IFP-II - Paciente: {nome}"
    corpo = f"Avaliação IFP-II (Inventário Fatorial de Personalidade) concluída.\n\n"
    corpo += f"=== DADOS DO(A) PACIENTE ===\nNome: {nome}\nSexo Biológico: {sexo}\nToken de Validação: {token}\n\n"
    corpo += "================ RESULTADOS ================\n\n"

    for fator, dados in resultados_processados.items():
        corpo += f"{fator}:\n  - Escore Bruto: {dados['bruto']}\n  - Percentil: {dados['percentil']}\n  - Classificação: {dados['classificacao']}\n\n"

    msg = MIMEMultipart()
    msg['From'] = SEU_EMAIL
    msg['To'] = "psicologabrunaligoski@gmail.com"
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SEU_EMAIL, SENHA_DO_EMAIL)
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

# ESTRUTURA E TABELAS
mapa_fatores = {
    'Assistência': [9, 44, 47, 58, 73, 77, 89, 98],
    'Intracepção': [18, 22, 25, 60, 67, 87, 90],
    'Afago': [17, 29, 31, 53, 54, 56, 97],
    'Deferência': [6, 15, 28, 48, 49, 50, 68, 82, 83],
    'Afiliação': [19, 26, 34, 37, 46, 52, 57, 64, 66],
    'Dominância': [11, 35, 45, 62, 65, 75, 81],
    'Desempenho': [2, 7, 12, 32, 33, 38, 80, 84, 86],
    'Exibição': [61, 71, 72, 85, 88, 93, 96, 99, 100],
    'Agressão': [23, 24, 39, 70, 76],
    'Ordem': [30, 51, 55, 78, 94, 95],
    'Persistência': [8, 10, 14, 16, 20, 27, 36, 42],
    'Mudança': [3, 13, 21, 41, 43, 59, 79],
    'Autonomia': [1, 4, 5, 40, 63, 69, 74, 91, 92]
}

tabelas_normativas = {
    "Masculino": {
        "Assistência": [(34, 5), (36, 10), (38, 15), (39, 20), (40, 25), (41, 30), (42, 35), (43, 40), (43, 45), (44, 50), (45, 55), (46, 60), (47, 65), (47, 70), (48, 75), (50, 80), (51, 85), (52, 90), (54, 95), (56, 100)],
        "Intracepção": [(22, 5), (25, 10), (27, 15), (28, 20), (29, 25), (31, 30), (32, 35), (32, 40), (33, 45), (34, 50), (35, 55), (36, 60), (36, 65), (37, 70), (38, 75), (39, 80), (41, 85), (42, 90), (45, 95), (49, 100)],
        "Afago": [(18, 5), (21, 10), (23, 15), (25, 20), (26, 25), (27, 30), (29, 35), (30, 40), (30, 45), (31, 50), (32, 55), (33, 60), (34, 65), (35, 70), (36, 75), (37, 80), (38, 85), (40, 90), (43, 95), (49, 100)],
        "Deferência": [(36, 5), (39, 10), (41, 15), (43, 20), (44, 25), (45, 30), (46, 35), (47, 40), (48, 45), (49, 50), (50, 55), (50, 60), (51, 65), (52, 70), (53, 75), (54, 80), (55, 85), (57, 90), (59, 95), (63, 100)],
        "Afiliação": [(39, 5), (42, 10), (44, 15), (46, 20), (47, 25), (48, 30), (49, 35), (50, 40), (51, 45), (52, 50), (53, 55), (54, 60), (55, 65), (56, 70), (56, 75), (57, 80), (59, 85), (60, 90), (62, 95), (63, 100)],
        "Dominância": [(16, 5), (19, 10), (21, 15), (23, 20), (24, 25), (25, 30), (26, 35), (27, 40), (28, 45), (29, 50), (30, 55), (31, 60), (32, 65), (33, 70), (34, 75), (35, 80), (37, 85), (39, 90), (41, 95), (49, 100)],
        "Desempenho": [(39, 5), (42, 10), (44, 15), (46, 20), (47, 25), (48, 30), (49, 35), (50, 40), (51, 45), (52, 50), (53, 55), (54, 60), (54, 65), (55, 70), (56, 75), (57, 80), (58, 85), (59, 90), (61, 95), (63, 100)],
        "Exibição": [(17, 5), (20, 10), (23, 15), (25, 20), (26, 25), (27, 30), (29, 35), (30, 40), (31, 45), (32, 50), (33, 55), (34, 60), (35, 65), (36, 70), (38, 75), (39, 80), (41, 85), (43, 90), (47, 95), (61, 100)],
        "Agressão": [(5, 5), (5, 10), (5, 15), (6, 20), (6, 25), (7, 30), (7, 35), (8, 40), (9, 45), (9, 50), (10, 55), (11, 60), (11, 65), (12, 70), (13, 75), (14, 80), (16, 85), (17, 90), (20, 95), (35, 100)],
        "Ordem": [(27, 5), (29, 10), (30, 15), (31, 20), (32, 25), (33, 30), (34, 35), (35, 40), (35, 45), (36, 50), (37, 55), (37, 60), (38, 65), (39, 70), (40, 75), (40, 80), (41, 85), (42, 90), (42, 95), (42, 100)],
        "Persistência": [(32, 5), (35, 10), (36, 15), (38, 20), (39, 25), (40, 30), (41, 35), (42, 40), (42, 45), (43, 50), (44, 55), (45, 60), (46, 65), (47, 70), (48, 75), (48, 80), (50, 85), (51, 90), (53, 95), (56, 100)],
        "Mudança": [(23, 5), (26, 10), (28, 15), (29, 20), (31, 25), (32, 30), (33, 35), (34, 40), (34, 45), (35, 50), (36, 55), (37, 60), (38, 65), (39, 70), (40, 75), (41, 80), (42, 85), (43, 90), (46, 95), (49, 100)],
        "Autonomia": [(25, 5), (27, 10), (30, 15), (31, 20), (33, 25), (34, 30), (35, 35), (36, 40), (37, 45), (37, 50), (38, 55), (39, 60), (40, 65), (41, 70), (42, 75), (44, 80), (45, 85), (47, 90), (50, 95), (62, 100)],
        "AFET": [(191, 5), (204, 10), (213, 15), (219, 20), (224, 25), (229, 30), (233, 35), (237, 40), (240, 45), (243, 50), (247, 55), (251, 60), (255, 65), (259, 70), (264, 75), (268, 80), (274, 85), (282, 90), (293, 95), (322, 100)],
        "ORGAN": [(103, 5), (110, 10), (114, 15), (117, 20), (120, 25), (122, 30), (124, 35), (127, 40), (129, 45), (131, 50), (133, 55), (134, 60), (137, 65), (138, 70), (141, 75), (143, 80), (145, 85), (148, 90), (152, 95), (161, 100)],
        "CON-OP": [(73, 5), (81, 10), (86, 15), (90, 20), (94, 25), (97, 30), (100, 35), (103, 40), (106, 45), (109, 50), (111, 55), (114, 60), (117, 65), (120, 70), (123, 75), (127, 80), (131, 85), (137, 90), (145, 95), (190, 100)]
    },
    "Feminino": {
        "Assistência": [(36, 5), (38, 10), (40, 15), (41, 20), (41, 25), (42, 30), (43, 35), (44, 40), (45, 45), (45, 50), (46, 55), (47, 60), (48, 65), (49, 70), (50, 75), (51, 80), (52, 85), (53, 90), (55, 95), (56, 100)],
        "Intracepção": [(23, 5), (26, 10), (28, 15), (29, 20), (31, 25), (32, 30), (33, 35), (34, 40), (34, 45), (35, 50), (36, 55), (37, 60), (37, 65), (38, 70), (39, 75), (40, 80), (42, 85), (43, 90), (45, 95), (49, 100)],
        "Afago": [(21, 5), (24, 10), (26, 15), (27, 20), (29, 25), (30, 30), (31, 35), (31, 40), (32, 45), (33, 50), (34, 55), (35, 60), (35, 65), (36, 70), (37, 75), (39, 80), (40, 85), (42, 90), (44, 95), (49, 100)],
        "Deferência": [(37, 5), (40, 10), (42, 15), (43, 20), (44, 25), (45, 30), (46, 35), (47, 40), (48, 45), (49, 50), (50, 55), (51, 60), (51, 65), (52, 70), (53, 75), (54, 80), (55, 85), (57, 90), (59, 95), (63, 100)],
        "Afiliação": [(41, 5), (44, 10), (46, 15), (47, 20), (49, 25), (50, 30), (51, 35), (52, 40), (53, 45), (53, 50), (54, 55), (55, 60), (56, 65), (57, 70), (58, 75), (59, 80), (60, 85), (61, 90), (62, 95), (63, 100)],
        "Dominância": [(13, 5), (17, 10), (19, 15), (21, 20), (22, 25), (24, 30), (25, 35), (26, 40), (27, 45), (28, 50), (29, 55), (30, 60), (31, 65), (31, 70), (32, 75), (34, 80), (35, 85), (37, 90), (40, 95), (49, 100)],
        "Desempenho": [(38, 5), (42, 10), (44, 15), (45, 20), (47, 25), (48, 30), (49, 35), (49, 40), (50, 45), (51, 50), (52, 55), (53, 60), (54, 65), (55, 70), (56, 75), (57, 80), (57, 85), (59, 90), (60, 95), (63, 100)],
        "Exibição": [(16, 5), (19, 10), (21, 15), (23, 20), (25, 25), (26, 30), (27, 35), (28, 40), (29, 45), (31, 50), (32, 55), (33, 60), (34, 65), (35, 70), (37, 75), (38, 80), (40, 85), (42, 90), (46, 95), (63, 100)],
        "Agressão": [(5, 5), (5, 10), (5, 15), (6, 20), (6, 25), (7, 30), (8, 35), (8, 40), (9, 45), (9, 50), (10, 55), (11, 60), (12, 65), (12, 70), (13, 75), (15, 80), (16, 85), (18, 90), (21, 95), (35, 100)],
        "Ordem": [(27, 5), (29, 10), (30, 15), (31, 20), (32, 25), (33, 30), (34, 35), (35, 40), (35, 45), (36, 50), (37, 55), (37, 60), (38, 65), (39, 70), (40, 75), (40, 80), (41, 85), (42, 90), (42, 95), (42, 100)],
        "Persistência": [(33, 5), (35, 10), (37, 15), (38, 20), (39, 25), (40, 30), (41, 35), (42, 40), (43, 45), (44, 50), (44, 55), (45, 60), (46, 65), (47, 70), (48, 75), (49, 80), (50, 85), (51, 90), (53, 95), (56, 100)],
        "Mudança": [(24, 5), (27, 10), (29, 15), (31, 20), (32, 25), (33, 30), (34, 35), (35, 40), (35, 45), (36, 50), (37, 55), (38, 60), (39, 65), (39, 70), (40, 75), (42, 80), (43, 85), (44, 90), (46, 95), (49, 100)],
        "Autonomia": [(25, 5), (28, 10), (30, 15), (31, 20), (33, 25), (34, 30), (35, 35), (36, 40), (37, 45), (38, 50), (38, 55), (39, 60), (40, 65), (41, 70), (42, 75), (44, 80), (45, 85), (47, 90), (50, 95), (62, 100)],
        "AFET": [(203, 5), (214, 10), (221, 15), (227, 20), (232, 25), (236, 30), (240, 35), (244, 40), (248, 45), (251, 50), (255, 55), (258, 60), (262, 65), (265, 70), (270, 75), (273, 80), (279, 85), (285, 90), (294, 95), (326, 100)],
        "ORGAN": [(104, 5), (110, 10), (114, 15), (117, 20), (120, 25), (122, 30), (125, 35), (127, 40), (129, 45), (131, 50), (133, 55), (135, 60), (136, 65), (138, 70), (140, 75), (142, 80), (144, 85), (147, 90), (151, 95), (161, 100)],
        "CON-OP": [(70, 5), (78, 10), (84, 15), (87, 20), (91, 25), (94, 30), (98, 35), (100, 40), (103, 45), (106, 50), (108, 55), (111, 60), (114, 65), (117, 70), (120, 75), (124, 80), (128, 85), (134, 90), (145, 95), (192, 100)]
    }
}

def obter_classificacao(percentil):
    if percentil <= 25: return "Baixo"
    if percentil <= 75: return "Médio"
    return "Alto"

def cruzar_dados_normativos(fator, pontuacao_bruta, sexo):
    tabela = tabelas_normativas[sexo][fator]
    percentil_encontrado = tabela[0][1]
    for score_tabela, perc in tabela:
        if pontuacao_bruta >= score_tabela:
            percentil_encontrado = perc
        else: break
    return percentil_encontrado, obter_classificacao(percentil_encontrado)

opcoes_respostas = {
    "1 - Nada característico": 1, "2 - Muito pouco característico": 2, "3 - Pouco característico": 3,
    "4 - Indiferente": 4, "5 - Característico": 5, "6 - Muito característico": 6, "7 - Totalmente característico": 7
}

# CONFIGURAÇÕES DE INTERFACE
st.set_page_config(page_title="Avaliação IFP-II", layout="centered")

st.markdown("""
    <style>
    div[data-testid="stFormSubmitButton"] > button {
        background-color: #0047AB !important;
        color: white !important;
        border: none !important;
        padding: 0.6rem 2.5rem !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        font-size: 16px !important;
    }
    div[data-testid="stFormSubmitButton"] > button:hover {
        background-color: #003380 !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

if "avaliacao_concluida" not in st.session_state:
    st.session_state.avaliacao_concluida = False

# Título Centralizado
st.markdown("<h1 style='text-align: center;'>Clínica de Psicologia e Psicanálise Bruna Ligoski</h1>", unsafe_allow_html=True)

if st.session_state.avaliacao_concluida:
    st.success("Avaliação concluída e enviada com sucesso! Muito obrigado(a) pela sua colaboração.")
    st.stop()

# ================= VALIDAÇÃO SILENCIOSA DO TOKEN =================
parametros = st.query_params
token_url = parametros.get("token", None)

if not token_url:
    st.warning("⚠️ Link de acesso inválido. Solicite um novo link à profissional.")
    st.stop()

try:
    registros = planilha.get_all_records()
    dados_token = None
    linha_alvo = 2 
    for i, reg in enumerate(registros):
        if str(reg.get("Token")) == token_url:
            dados_token = reg
            linha_alvo += i
            break
            
    if not dados_token or dados_token.get("Status") != "Aberto":
        st.error("⚠️ Este link é inválido ou já foi utilizado.")
        st.stop()
except Exception:
    st.error("Erro técnico na validação do link.")
    st.stop()

# ================= QUESTIONÁRIO IFP-II =================
linha_fina = "<hr style='margin-top: 8px; margin-bottom: 8px;'/>"
st.markdown(linha_fina, unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>Inventário Fatorial de Personalidade (IFP-II)</h3>", unsafe_allow_html=True)
st.markdown(linha_fina, unsafe_allow_html=True)

st.write("Este questionário descreve sentimentos e jeitos de ser. Não há respostas certas ou erradas; responda de acordo com como você se sente **atualmente**.")
st.markdown(linha_fina, unsafe_allow_html=True)

perguntas = [
    "1. Gosto de fazer coisas que outras pessoas consideram fora do comum.", "2. Gostaria de realizar um grande feito ou grande obra na minha vida.", "3. Gosto de experimentar novidades e mudanças em meu dia-a-dia.", "4. Não gosto de situações em que se exige que eu me comporte de determinada maneira.", "5. Gosto de dizer o que eu penso a respeito das coisas.", "6. Gosto de saber o que grandes personalidades disseram sobre os problemas pelos quais eu me interesso.", "7. Gosto de ser capaz de fazer as coisas melhor do que as outras pessoas.", "8. Gosto de concluir qualquer trabalho ou tarefa que tenha começado.", "9. Gosto de ajudar meus amigos quando eles estão com problemas.", "10. Não costumo abandonar um quebra-cabeça ou problema antes que consiga resolvê-lo.", "11. Gosto de dizer aos outros como fazer seus trabalhos.", "12. Gostaria de ser considerado(a) uma autoridade em algum trabalho, profissão ou campo de especialização.", "13. Gosto de experimentar e provar coisas novas.", "14. Quando tenho alguma tarefa para fazer, gosto de começar logo e permanecer trabalhando até completá-la.", "15. Aceito com prazer a liderança das pessoas que admiro.", "16. Gosto de trabalhar horas a fio sem ser interrompido(a).", "17. Gosto que meus amigos me dêem muita atenção quando estou sofrendo ou doente.", "18. Costumo analisar minhas intenções e sentimentos.", "19. Gosto de fazer com carinho pequenos favores a meus amigos.", "20. Gosto de ficar acordado(a) até tarde para terminar um trabalho.", "21. Gosto de andar pelo país e viver em lugares diferentes.", "22. Gosto de analisar os sentimentos e intenções dos outros.", "23. Gosto de fazer gozação com pessoas que fazem coisas que eu considero estúpidas.", "24. Tenho vontade de me vingar quando alguém me insulta.", "25. Gosto de pensar sobre o caráter dos meus amigos e tentar descobrir o que os faz serem como são.", "26. Sou leal aos meus amigos.", "27. Gosto de levar um trabalho ou tarefa até o fim antes de começar outro.", "28. Gosto de dizer aos meus superiores que eles fizeram um bom trabalho, quando acredito nisso.", "29. Gosto que meus amigos sejam solidários comigo e me animem quando estou deprimido(a).", "30. Antes de começar um trabalho, gosto de organizá-lo e planejá-lo.", "31. Gosto que meus amigos demonstrem muito afeto por mim.", "32. Gosto de realizar tarefas que, na opinião dos outros, exigem habilidade e esforço.", "33. Gosto de ser bem-sucedido nas coisas que faço.", "34. Gosto de fazer amizades.", "35. Gosto de ser considerado(a) um(a) líder pelos outros.", "36. Gosto de realizar com afinco (sem descanso) qualquer trabalho que faço.", "37. Gosto de participar de grupos cujos membros se tratem com afeto e amizade.", "38. Sinto-me satisfeito(a) quando realizo bem um trabalho difícil.", "39. Tenho vontade de mandar os outros calarem a boca quando discordo deles.", "40. Gosto de fazer coisas do meu jeito sem me importar com o que os outros possam pensar.", "41. Gosto de viajar e conhecer o país.", "42. Gosto de me fixar em um trabalho ou problema mesmo quando a solução pareça extremamente difícil.", "43. Gosto de conhecer novas pessoas.", "44. Gosto de dividir coisas com os outros.", "45. Sinto-me satisfeito(a) quando consigo convencer e influenciar ou outros.", "46. Gosto de demonstrar muita afeição por meus amigos.", "47. Gosto de prestar favores aos outros.", "48. Gosto de seguir instruções e fazer o que é esperado de mim.", "49. Gosto de elogiar alguém que admiro.", "50. Quando planejo alguma coisa, procuro sugestões de pessoas que respeito.", "51. Gosto de manter minhas coisas limpas e ordenadas em minha escrivaninha ou em meu local de trabalho.", "52. Gosto de manter fortes laços de amizade.", "53. Gosto que meus amigos me ajudem quando estou com problema.", "54. Gosto que meus amigos mostrem boa vontade em me prestar pequenos favores.", "55. Gosto de manter minhas cartas, contas e outros papéis bem arrumados e arquivados de acordo com algum sistema.", "56. Gosto que meus amigos sejam solidários e compreensivos quando tenho problemas.", "57. Prefiro fazer coisas com meus amigos a fazer sozinho.", "58. Gosto de tratar outras pessoas com bondade e compaixão.", "59. Gosto de comer em restaurantes novos e exóticos (diferentes).", "60. Procuro entender como meus amigos se sentem a respeito de problemas que eles enfrentam.", "61. Gosto de ser o centro das atenções em um grupo.", "62. Gosto de ser um dos líderes nas organizações e grupos aos quais pertenço.", "63. Gosto de ser independente dos outros para decidir o que quero fazer.", "64. Gosto de me manter em contato com meus amigos.", "65. Quando participo de uma comissão (reunião), gosto de ser indicado ou eleito presidente.", "66. Gosto de fazer tantos amigos quanto possível.", "67. Gosto de observar como uma outra pessoa se sente numa determinada situação.", "68. Quando estou em um grupo, aceito com prazer a liderança de outra pessoa para decidir o que o grupo fará.", "69. Não gosto de me sentir pressionado(a) por responsabilidades e deveres.", "70. Às vezes, fico tão irritado(a) que sinto vontade de jogar e quebrar coisas.", "71. Gosto de fazer perguntas que ninguém será capaz de responder.", "72. Às vezes, gosto de fazer coisas simplesmente para ver o efeito que terão sobre os outros.", "73. Sou solidário com meus amigos quando machucados ou doentes.", "74. Não tenho medo de criticar pessoas que ocupam posições de autoridade.", "75. Gosto de fiscalizar e dirigir os atos dos outros sempre que posso.", "76. Culpo os outros quando as coisas dão errado comigo.", "77. Gosto de ajudar pessoas que têm menos sorte do que eu.", "78. Gosto de planejar e organizar, em todos os detalhes, qualquer trabalho que eu faço.", "79. Gosto de fazer coisas novas e diferentes.", "80. Gostaria de realizar com sucesso alguma coisa de grande importância.", "81. Quando estou com um grupo de pessoas. gosto de decidir sobre o que vamos fazer.", "82. Interesso-me em conhecer a vida de grandes personalidades.", "83. Procuro me adaptar ao modo de ser das pessoas que admiro.", "84. Gosto de resolver quebra-cabeças e problemas com os quais outras pessoas têm dificuldades.", "85. Gosto de falar sobre os meus sucessos.", "86. Gosto de dar o melhor de mim em tudo que faço.", "87. Gosto de estudar e analisar o comportamento dos outros.", "88. Gosto de contar aos outros aventuras e coisas estranhas que aconteceram comigo.", "89. Perdão as pessoas que às vezes possam me magoar.", "90. Gosto de prever (entender) como meus amigos irão agir em diferentes situações.", "91. Gosto de me sentir livre para fazer o que quero.", "92. Gosto de me sentir livre para ir e vir quando quiser.", "93. Gosto de usar palavras cujo significado as outras pessoas desconhecem.", "94. Gosto de planejar antes de iniciar algo difícil.", "95. Qualquer trabalho escrito que faço, gosto que seja preciso, limpo e bem-organizado.", "96. Gosto que as pessoas notem e comentem a minha aparência quando estou em público.", "97. Gosto que meus amigos me tratem com delicadeza.", "98. Gosto de ser generoso(a) con os outros.", "99. Gosto de contar histórias e piadas engraçadas em festas.", "100. Gosto de dizer coisas que os outros consideram engraçadas e inteligentes."
]

with st.form("form_ifp"):
    st.subheader("Identificação do(a) Paciente")
    nome_paciente = st.text_input("Nome Completo *")
    sexo_paciente = st.selectbox("Sexo Biológico *", ["Selecione", "Masculino", "Feminino"])
    
    # ================= BLOCO 2: CHAMADA DA MARCA D'ÁGUA =================
    inject_watermark(nome_paciente, token_url)
    # ====================================================================

    st.divider()

    respostas_usuario = {}
    for i, texto in enumerate(perguntas):
        num_q = i + 1
        st.write(f"**{texto}**")
        respostas_usuario[num_q] = st.radio(f"q_{num_q}", list(opcoes_respostas.keys()), index=None, label_visibility="collapsed")
        st.divider()

    if st.form_submit_button("Enviar Avaliação"):
        if not nome_paciente or sexo_paciente == "Selecione" or any(r is None for r in respostas_usuario.values()):
            st.error("Por favor, preencha todos os campos e responda todas as questões.")
        else:
            escores = {f: 0 for f in list(mapa_fatores.keys()) + ['AFET', 'ORGAN', 'CON-OP']}
            for n, r in respostas_usuario.items():
                val = opcoes_respostas[r]
                for f, qs in mapa_fatores.items():
                    if n in qs: escores[f] += val

            escores['AFET'] = escores['Deferência'] + escores['Persistência'] + escores['Autonomia']
            escores['ORGAN'] = escores['Assistência'] + escores['Persistência'] + escores['Autonomia']
            escores['CON-OP'] = escores['Deferência'] + escores['Mudança'] + escores['Autonomia']

            resultados_processados = {f: cruzar_dados_normativos(f, v, sexo_paciente) for f, v in escores.items()}
            res_dict = {f: {"bruto": escores[f], "percentil": resultados_processados[f][0], "classificacao": resultados_processados[f][1]} for f in escores}

            with st.spinner('Enviando avaliação...'):
                if enviar_email_resultados(nome_paciente, token_url, sexo_paciente, res_dict):
                    try:
                        planilha.update_cell(linha_alvo, 5, "Respondido")
                        st.session_state.avaliacao_concluida = True
                        st.rerun()
                    except:
                        st.session_state.avaliacao_concluida = True
                        st.rerun()
                else:
                    st.error("Houve um erro no envio. Tente novamente.")
