import subprocess
import sys
import pandas as pd
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Servidor do Assistente de Dashboards")
MAX_MB = 10

@mcp.tool()
def upload_csv(file_path: str) -> dict:
    """Valida um arquivo CSV e retorna um resumo das colunas"""

    file_path_object = Path(file_path)
    tamanho_mb_arquivo = file_path_object.stat().st_size / (1024 * 1024)~

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
def exibe_cartao(csv_path: str, coluna: str, agregacao: str = None) -> dict:
    """Exibe um cartão com métrica agregada (total, média, contagem, máimo e/ou mínimo)"""

    file_path_object = Path(csv_path)

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
    return {"ok": True, "resultado": resultado}
