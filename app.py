import pandas as pd
import streamlit as st
import io
import zipfile

# --- Funções (mesmas do código anterior) ---
PADROES_VALIDOS = ("1;", "2;", "3;", "4;")

def starts_valid(line: str) -> bool:
    if line is None:
        return False
    return line.lstrip().lstrip("\ufeff").startswith(PADROES_VALIDOS)

def verificar_linhas_quebradas_conteudo(conteudo: str):
    linhas_quebradas = []
    for numero_linha, linha in enumerate(conteudo.splitlines(), start=1):
        texto = linha.rstrip("\n")
        if texto.strip() == "":
            continue
        if not starts_valid(texto):
            linhas_quebradas.append(numero_linha)
    return linhas_quebradas

def corrigir_quebras_conteudo(conteudo: str):
    linhas = conteudo.splitlines()
    linhas_corrigidas = []
    merges = []
    last_start_line_num = None

    for idx, linha in enumerate(linhas, start=1):
        raw = linha.rstrip("\n")
        if raw.strip() == "":
            continue
        if starts_valid(raw):
            linhas_corrigidas.append(raw.strip())
            last_start_line_num = idx
        else:
            if linhas_corrigidas and last_start_line_num is not None:
                anexado = raw.strip()
                linhas_corrigidas[-1] += " " + anexado
                merges.append((last_start_line_num, idx, anexado))
            else:
                linhas_corrigidas.append(raw.strip())
                last_start_line_num = idx

    conteudo_corrigido = "\n".join(linhas_corrigidas)
    return conteudo_corrigido, merges

def contar_linhas(conteudo: str):
    linhas = conteudo.splitlines()
    total = len(linhas)
    nao_vazias = sum(1 for l in linhas if l.strip() != "")
    return total, nao_vazias

# -------------------------
# App Streamlit
# -------------------------
st.set_page_config(page_title="Corretor de Linhas Quebradas (TXT)", layout="wide")
st.title("📄 Corretor de Linhas Quebradas — TXT (padrão: 1;,2;,3;,4;)")

st.write("Envie um ou mais arquivos .txt. O app mostrará um resumo das linhas quebradas antes da correção e permitirá baixar todos os arquivos corrigidos em um ZIP.")

uploaded_files = st.file_uploader(
    "Envie seu(s) arquivo(s) .txt",
    type=["txt"],
    accept_multiple_files=True
)

if not uploaded_files:
    st.info("Faça upload de um ou mais arquivos .txt para começar.")
    st.stop()

if st.button("🛠️ Corrigir todos os arquivos e gerar ZIP"):
    # Criar buffer do ZIP em memória
    zip_buffer = io.BytesIO()
    resumo_lista = []

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for uploaded in uploaded_files:
            conteudo = uploaded.getvalue().decode("utf-8", errors="ignore")

            # --- Resumo antes da correção ---
            total_linhas, linhas_nao_vazias = contar_linhas(conteudo)
            linhas_quebradas_antes = verificar_linhas_quebradas_conteudo(conteudo)

            # --- Corrigir ---
            corrigido_texto, merges = corrigir_quebras_conteudo(conteudo)
            linhas_quebradas_depois = verificar_linhas_quebradas_conteudo(corrigido_texto)

            # Adiciona arquivo corrigido ao ZIP
            zip_file.writestr(f"{uploaded.name[:-4]}_corrigido.txt", corrigido_texto)

            # Adiciona ao resumo
            resumo_lista.append({
                "Arquivo": uploaded.name,
                "Linhas totais": total_linhas,
                "Linhas não vazias": linhas_nao_vazias,
                "Linhas quebradas antes": len(linhas_quebradas_antes),
                "Números das linhas quebradas antes": linhas_quebradas_antes,
                "Linhas quebradas depois": len(linhas_quebradas_depois)
            })

    # Exibir resumo final como tabela
    st.subheader("📊 Resumo por arquivo")
    resumo_df = pd.DataFrame(resumo_lista)
    st.dataframe(resumo_df)

    # Botão para download do ZIP
    zip_buffer.seek(0)
    st.download_button(
        label="⬇ Baixar todos os arquivos corrigidos (ZIP)",
        data=zip_buffer,
        file_name="arquivos_corrigidos.zip",
        mime="application/zip"
    )
