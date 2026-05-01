import os

extensoes = {".py", ".yml", ".yaml", ".txt", ".md", ".js", ".html", ".css", ".json"}
excluir_pastas = {"venv", ".git", "__pycache__", "node_modules", ".venv", "env"}
arquivos_especiais = {"Dockerfile", "docker-compose.yml", ".env.example", "requirements.txt"}
saida = "dump_completo.txt"

def listar_estrutura(diretorio, nivel=0):
    linhas = []
    for item in sorted(os.listdir(diretorio)):
        caminho = os.path.join(diretorio, item)
        if item in excluir_pastas or item.startswith("."):
            continue
        if os.path.isdir(caminho):
            linhas.append("    " * nivel + f"[DIR]  {item}/")
            linhas.extend(listar_estrutura(caminho, nivel + 1))
        else:
            linhas.append("    " * nivel + f"[FILE] {item}")
    return linhas

def dump_conteudo(caminho_arquivo):
    try:
        with open(caminho_arquivo, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except:
        return "[ERRO: Não foi possível ler o arquivo]"

with open(saida, "w", encoding="utf-8") as out:
    # 1. Estrutura
    out.write("ESTRUTURA DO PROJETO\n")
    out.write("=" * 80 + "\n")
    for linha in listar_estrutura("."):
        out.write(linha + "\n")

    out.write("\n\nCONTEÚDO DOS ARQUIVOS\n")
    out.write("=" * 80 + "\n")

    # 2. Conteúdo
    for raiz, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in excluir_pastas and not d.startswith(".")]
        for arquivo in sorted(files):
            ext = os.path.splitext(arquivo)[1].lower()
            if ext in extensoes or arquivo in arquivos_especiais:
                caminho = os.path.join(raiz, arquivo)
                out.write(f"\n\n========== {caminho} ==========\n\n")
                out.write(dump_conteudo(caminho))