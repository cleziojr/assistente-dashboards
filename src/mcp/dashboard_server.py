import base64
import shutil
import time
import pandas as pd
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Servidor do Assistente de Dashboards")
MAX_MB = 10
MAX_BYTES_BASE64 = MAX_MB * 1024 * 1024
TEMPO_EXPIRACAO_SEGUNDOS = 3600
EXTENSOES_PERMITIDAS = {".csv"}
DATA_DIRETORIO = Path(__file__).resolve().parents[2] / "data"


def limpar_sessoes_expiradas():
    agora = time.time()
    for subdir in DATA_DIRETORIO.iterdir():
        if subdir.is_dir() and agora - subdir.stat().st_mtime > TEMPO_EXPIRACAO_SEGUNDOS:
            shutil.rmtree(subdir, ignore_errors=True)


def valida_caminho_arquivo(caminho_arquivo: Path) -> str | None:
    """Retorna mensagem de erro se o caminho não estiver em data/, ou None se válido."""
    if not str(caminho_arquivo.resolve()).startswith(str(DATA_DIRETORIO)):
        return "Acesso negado"
    return None


@mcp.tool()
def upload_csv(file_path: str) -> dict:
    """Valida um arquivo CSV e retorna um resumo das colunas"""

    limpar_sessoes_expiradas()
    file_path_object = Path(file_path).resolve()

    erro_caminho = valida_caminho_arquivo(file_path_object)
    if erro_caminho:
        return {"ok": False, "error": erro_caminho}

    tamanho_mb_arquivo = file_path_object.stat().st_size / (1024 * 1024) if file_path_object.exists() else 0

    if not file_path_object.exists():
        return {"ok": False, "error": f"Arquivo não encontrado {file_path}. Verifique o caminho e tente novamente"}

    if tamanho_mb_arquivo > MAX_MB:
        return {"ok": False, "error": f"Arquivo muito grande ({tamanho_mb_arquivo:.1f} MB). O limite é {MAX_MB} MB."}

    if file_path_object.suffix.lower() != ".csv":
        return {"ok": False, "error": f"O aquivo deve ser um CSV"}

    df = pd.read_csv(file_path_object)

    resumo_dados_arquivo = {
        coluna: {
            "tipo_dado": str(df[coluna].dtype),
            "quantidade_valores_nulos": int(df[coluna].isna()).sum(),
            "exemplos_valores": df[coluna].dropna().sample(3).tolist()
        } for coluna in df.columns
    }

    return {"ok": True, "resumo_dados_arquivo": resumo_dados_arquivo}

@mcp.tool()
def efetua_agregacao_dados(csv_path: str, coluna: str, agregacao: str = None) -> dict:
    """Agrega dados de uma coluna específica de um arquivo CSV. As operações suportadas são: total, média, contagem, máximo e mínimo"""

    limpar_sessoes_expiradas()
    file_path_object = Path(csv_path).resolve()

    erro_caminho = valida_caminho_arquivo(file_path_object)
    if erro_caminho:
        return {"ok": False, "error": erro_caminho}

    if not file_path_object.exists():
        return {"ok": False, "error": f"Arquivo não encontrado. Verifique o caminho do arquivo e tente novamente"}

    df = pd.read_csv(file_path_object)
    if coluna not in df.columns:
        return {"ok": False, "error": f"A coluna que o usuário solicitou para efetuar a agregação não existe no conjunto de dados importado"}

    operacao = {"total": df[coluna].sum(),
                "media": df[coluna].mean(),
                "contagem": df[coluna].count(),
                "maximo": df[coluna].max(),
                "minimo": df[coluna].min()
                }

    if agregacao not in operacao:
        return {"ok": False, "error": f"A agregação solicitada não é suportada. As opções válidas são: {list(operacao.keys())}"}

    resultado = operacao[agregacao]()

    return {"ok": True, "tipo": "Cartão", "coluna": coluna, "agregacao": agregacao, "resultado": round(float(resultado), 2)}

@mcp.tool()
def estrutura_dados_barras_verticais(csv_path: str, eixo_x: str, eixo_y: str) -> dict:
    """Estrutura os dados de um arquivo CSV para gerar um gráfico de barras verticais"""

    limpar_sessoes_expiradas()
    file_path_object = Path(csv_path).resolve()

    erro_caminho = valida_caminho_arquivo(file_path_object)
    if erro_caminho:
        return {"ok": False, "error": erro_caminho}

    if not file_path_object.exists():
        return {"ok": False, "error": f"Arquivo não encontrado. Verifique o caminho do arquivo e tente novamente"}

    df = pd.read_csv(file_path_object)
    for coluna in [eixo_x, eixo_y]:
        if coluna not in df.columns:
            return {"ok": False, "error": f"A coluna '{coluna}' não existe no conjunto de dados importado"}

    dados_agrupados = df.groupby(eixo_x)[eixo_y].sum().reset_index()

    return {"ok": True, "tipo": "barras_verticais", "x": eixo_x, "y": eixo_y, "dados_agrupados": dados_agrupados.to_dict(orient="records")}

@mcp.tool()
def estrutura_dados_barras_horizontais(csv_path: str, eixo_x: str, eixo_y: str) -> dict:
    """Estrutura os dados de um arquivo CSV para gerar um gráfico de barras horizontais"""

    limpar_sessoes_expiradas()
    file_path_object = Path(csv_path).resolve()

    erro_caminho = valida_caminho_arquivo(file_path_object)
    if erro_caminho:
        return {"ok": False, "error": erro_caminho}

    if not file_path_object.exists():
        return {"ok": False, "error": f"Arquivo não encontrado. Verifique o caminho do arquivo e tente novamente"}

    df = pd.read_csv(file_path_object)
    for coluna in [eixo_x, eixo_y]:
        if coluna not in df.columns:
            return {"ok": False, "error": f"A coluna '{coluna}' não existe no conjunto de dados importado"}

    dados_agrupados = df.groupby(eixo_x)[eixo_y].sum().reset_index()

    return {"ok": True, "tipo": "barras_horizontais", "x": eixo_x, "y": eixo_y, "dados_agrupados": dados_agrupados.to_dict(orient="records")}


@mcp.tool()
def upload_csv_bytes(nome_arquivo: str, conteudo_base64: str) -> dict:
    """Recebe um CSV codificado em base64, valida e salva em data/ para uso nas demais ferramentas."""
    limpar_sessoes_expiradas()

    if Path(nome_arquivo).suffix.lower() not in EXTENSOES_PERMITIDAS:
        return {"ok": False, "error": f"Apenas arquivos CSV são permitidos. Extensão recebida: '{Path(nome_arquivo).suffix}'"}

    if len(conteudo_base64) > MAX_BYTES_BASE64 * 1.4:
        return {"ok": False, "error": f"Arquivo muito grande. O limite é {MAX_MB} MB."}

    try:
        conteudo = base64.b64decode(conteudo_base64)
    except Exception:
        return {"ok": False, "error": "Conteúdo base64 inválido. Verifique a codificação e tente novamente."}

    tamanho_mb = len(conteudo) / (1024 * 1024)
    if tamanho_mb > MAX_MB:
        return {"ok": False, "error": f"Arquivo muito grande ({tamanho_mb:.1f} MB). O limite é {MAX_MB} MB."}

    DATA_DIRETORIO.mkdir(parents=True, exist_ok=True)
    destino = (DATA_DIRETORIO / Path(nome_arquivo).name).resolve()

    erro_caminho = valida_caminho_arquivo(destino)
    if erro_caminho:
        return {"ok": False, "error": erro_caminho}

    destino.write_bytes(conteudo)

    return {"ok": True, "caminho": str(destino), "mensagem": f"Arquivo salvo. Use o caminho '{destino}' nas demais ferramentas."}


if __name__ == "__main__":
    mcp.run()
