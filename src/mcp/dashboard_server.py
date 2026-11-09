import os
import sys
import json
import base64
import shutil
import socket
import subprocess
import time
import pandas as pd
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

PROJETO_RAIZ = Path(__file__).resolve().parents[2]

def streamlit_exe() -> str:
    """Localiza o streamlit.exe no mesmo virtualenv que está rodando este processo."""
    scripts_dir = Path(sys.executable).parent
    for nome in ["streamlit.exe", "streamlit"]:
        candidato = scripts_dir / nome
        if candidato.exists():
            return str(candidato)
    return shutil.which("streamlit") or "streamlit"

STREAMLIT_EXE = streamlit_exe()

load_dotenv()

mcp = FastMCP("Servidor do Assistente de Dashboards")
MAX_MB = 10
MAX_BYTES_BASE64 = MAX_MB * 1024 * 1024
TEMPO_EXPIRACAO_SEGUNDOS = 3600
EXTENSOES_PERMITIDAS = {".csv"}
DATA_DIRETORIO = Path(__file__).resolve().parents[2] / "data"
SCRIPTS_DIRETORIO = Path(__file__).resolve().parents[2] / "apps_gerados"

ENDERECO_STREAMLIT = (
    "0.0.0.0" if os.getenv("STREAMLIT_ENV", "development") == "production" else "localhost"
)


def encontrar_porta_livre() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def limpar_sessoes_expiradas():
    agora = time.time()
    for subdir in DATA_DIRETORIO.iterdir():
        if subdir.is_dir() and agora - subdir.stat().st_mtime > TEMPO_EXPIRACAO_SEGUNDOS:
            shutil.rmtree(subdir, ignore_errors=True)


MAX_CATEGORIAS_EIXO_X = 50


def valida_caminho_arquivo(caminho_arquivo: Path) -> str | None:
    """Retorna mensagem de erro se o caminho não estiver em data/, ou None se válido."""
    if not str(caminho_arquivo.resolve()).startswith(str(DATA_DIRETORIO)):
        return "Acesso negado"
    return None


def ler_csv(caminho: Path) -> tuple[pd.DataFrame | None, str | None]:
    """Lê CSV com detecção automática de separador e encoding. Retorna (df, erro)."""
    for sep in [",", ";"]:
        for enc in ["utf-8", "latin-1"]:
            try:
                df = pd.read_csv(caminho, sep=sep, encoding=enc)
                if df.shape[1] > 1:
                    return df, None
            except (pd.errors.ParserError, UnicodeDecodeError):
                continue
    try:
        df = pd.read_csv(caminho, encoding="utf-8", on_bad_lines="skip")
        return df, None
    except Exception as e:
        return None, f"Não foi possível ler o arquivo CSV: {e}"


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

    df, erro_leitura = ler_csv(file_path_object)
    if erro_leitura:
        return {"ok": False, "error": erro_leitura}
    if df.empty:
        return {"ok": False, "error": "O arquivo CSV está vazio."}

    resumo_dados_arquivo = {
        coluna: {
            "tipo_dado": str(df[coluna].dtype),
            "quantidade_valores_nulos": int(df[coluna].isna().sum()),
            "exemplos_valores": df[coluna].dropna().head(3).tolist()
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

    df, erro_leitura = ler_csv(file_path_object)
    if erro_leitura:
        return {"ok": False, "error": erro_leitura}
    if df.empty:
        return {"ok": False, "error": "O arquivo CSV está vazio."}
    if coluna not in df.columns:
        return {"ok": False, "error": f"A coluna '{coluna}' não existe. Colunas disponíveis: {list(df.columns)}"}

    operacoes_numericas = {"total", "media", "maximo", "minimo"}
    if agregacao in operacoes_numericas and not pd.api.types.is_numeric_dtype(df[coluna]):
        return {"ok": False, "error": f"A operação '{agregacao}' exige coluna numérica. '{coluna}' é do tipo {df[coluna].dtype}. Colunas numéricas disponíveis: {[c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]}"}

    operacoes = {
        "total": lambda: df[coluna].sum(),
        "media": lambda: df[coluna].mean(),
        "contagem": lambda: df[coluna].count(),
        "maximo": lambda: df[coluna].max(),
        "minimo": lambda: df[coluna].min(),
    }

    if agregacao not in operacoes:
        return {"ok": False, "error": f"Agregação inválida. As opções são: {list(operacoes.keys())}"}

    resultado = operacoes[agregacao]()

    if pd.isna(resultado):
        return {"ok": False, "error": f"A coluna '{coluna}' contém apenas valores nulos. Não é possível calcular '{agregacao}'."}

    valor = float(resultado) if isinstance(resultado, (int, float)) else str(resultado)
    return {"ok": True, "tipo": "Cartão", "coluna": coluna, "agregacao": agregacao, "resultado": round(valor, 2) if isinstance(valor, float) else valor}

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

    df, erro_leitura = ler_csv(file_path_object)
    if erro_leitura:
        return {"ok": False, "error": erro_leitura}
    if df.empty:
        return {"ok": False, "error": "O arquivo CSV está vazio."}
    if eixo_x == eixo_y:
        return {"ok": False, "error": "Eixo X e eixo Y não podem ser a mesma coluna."}
    for coluna in [eixo_x, eixo_y]:
        if coluna not in df.columns:
            return {"ok": False, "error": f"A coluna '{coluna}' não existe. Colunas disponíveis: {list(df.columns)}"}
    if not pd.api.types.is_numeric_dtype(df[eixo_y]):
        return {"ok": False, "error": f"'{eixo_y}' não é numérica. Colunas numéricas disponíveis: {[c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]}"}
    if df[eixo_y].isna().all():
        return {"ok": False, "error": f"A coluna '{eixo_y}' contém apenas valores nulos."}

    cardinalidade = df[eixo_x].nunique()
    if cardinalidade > MAX_CATEGORIAS_EIXO_X:
        return {"ok": False, "error": f"A coluna '{eixo_x}' tem {cardinalidade} categorias únicas (limite: {MAX_CATEGORIAS_EIXO_X}). Escolha uma coluna com menos categorias ou aplique um filtro antes."}

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

    df, erro_leitura = ler_csv(file_path_object)
    if erro_leitura:
        return {"ok": False, "error": erro_leitura}
    if df.empty:
        return {"ok": False, "error": "O arquivo CSV está vazio."}
    if eixo_x == eixo_y:
        return {"ok": False, "error": "Eixo X e eixo Y não podem ser a mesma coluna."}
    for coluna in [eixo_x, eixo_y]:
        if coluna not in df.columns:
            return {"ok": False, "error": f"A coluna '{coluna}' não existe. Colunas disponíveis: {list(df.columns)}"}
    if not pd.api.types.is_numeric_dtype(df[eixo_y]):
        return {"ok": False, "error": f"'{eixo_y}' não é numérica. Colunas numéricas disponíveis: {[c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]}"}
    if df[eixo_y].isna().all():
        return {"ok": False, "error": f"A coluna '{eixo_y}' contém apenas valores nulos."}

    cardinalidade = df[eixo_x].nunique()
    if cardinalidade > MAX_CATEGORIAS_EIXO_X:
        return {"ok": False, "error": f"A coluna '{eixo_x}' tem {cardinalidade} categorias únicas (limite: {MAX_CATEGORIAS_EIXO_X}). Escolha uma coluna com menos categorias ou aplique um filtro antes."}

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


from src.mcp.templates import TEMPLATE_STREAMLIT, TEMPLATE_BARRAS_VERTICAIS, TEMPLATE_BARRAS_HORIZONTAIS, TEMPLATE_CARTAO


def aguarda_porta(porta: int, timeout: int = 25) -> bool:
    """Retorna True assim que a porta aceitar conexões TCP, ou False após o timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("localhost", porta), timeout=1):
                return True
        except OSError:
            time.sleep(1)
    return False


def lanca_streamlit_destacado(script_path: Path, porta: int) -> str | None:
    """Lança o Streamlit desacoplado do processo atual. Retorna mensagem de erro ou None.

    No Windows, o servidor MCP roda dentro de um Job Object com KILL_ON_JOB_CLOSE criado
    pelo SDK do MCP: qualquer filho direto morre quando o servidor MCP encerra. Para o
    dashboard sobreviver, ele é criado via WMI (Win32_Process.Create), que o instancia a
    partir do WmiPrvSE.exe (fora do Job Object do servidor MCP)
    """
    cmdline = (
        f'"{STREAMLIT_EXE}" run "{script_path}" '
        f'--server.port {porta} --server.address {ENDERECO_STREAMLIT} '
        f'--server.headless true --browser.gatherUsageStats false'
    )

    if sys.platform != "win32":
        try:
            subprocess.Popen(
                cmdline, shell=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
                cwd=str(PROJETO_RAIZ), start_new_session=True,
            )
            return None
        except Exception as e:
            return f"Falha ao lançar o servidor: {e}"

    comando_powershell = (
        "$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create "
        f"-Arguments @{{CommandLine='{cmdline}'; CurrentDirectory='{PROJETO_RAIZ}'}}; "
        "exit $r.ReturnValue"
    )
    try:
        resultado = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", comando_powershell],
            capture_output=True, text=True, timeout=30,
        )
    except Exception as e:
        return f"Falha ao invocar o lançador do servidor: {e}"

    if resultado.returncode != 0:
        return f"WMI retornou código {resultado.returncode} ao criar o processo. Detalhes: {resultado.stderr[:300]}"
    return None


@mcp.tool()
def gerar_app_streamlit(
    csv_path: str,
    tipo_grafico: str,
    eixo_x: str,
    eixo_y: str,
    titulo: str = "Dashboard",
    agregacao: str = "total",
) -> dict:
    """Gera um app Streamlit com o gráfico solicitado e retorna o link de acesso.
    tipo_grafico deve ser: barras_verticais, barras_horizontais ou cartao.
    agregacao é usado apenas para cartao: total, media, contagem, maximo, minimo."""
    limpar_sessoes_expiradas()

    tipos_validos = {"barras_verticais", "barras_horizontais", "cartao"}
    if tipo_grafico not in tipos_validos:
        return {"ok": False, "error": f"tipo_grafico deve ser um de: {tipos_validos}"}

    caminho = Path(csv_path).resolve()
    erro_caminho = valida_caminho_arquivo(caminho)
    if erro_caminho:
        return {"ok": False, "error": erro_caminho}
    if not caminho.exists():
        return {"ok": False, "error": "Arquivo CSV não encontrado."}

    if tipo_grafico == "barras_verticais":
        resultado = estrutura_dados_barras_verticais(csv_path, eixo_x, eixo_y)
    elif tipo_grafico == "barras_horizontais":
        resultado = estrutura_dados_barras_horizontais(csv_path, eixo_x, eixo_y)
    else:
        resultado = efetua_agregacao_dados(csv_path, eixo_y, agregacao)

    if not resultado.get("ok"):
        return resultado

    if tipo_grafico == "cartao":
        label = f"{agregacao.capitalize()} de {eixo_y}"
        codigo_grafico = TEMPLATE_CARTAO.format(
            label=label,
            valor=resultado.get("resultado", 0),
        )
        dados_json = "[]"
    else:
        dados_json = json.dumps(resultado["dados_agrupados"], ensure_ascii=False)
        template = TEMPLATE_BARRAS_VERTICAIS if tipo_grafico == "barras_verticais" else TEMPLATE_BARRAS_HORIZONTAIS
        codigo_grafico = template.format(eixo_x=eixo_x, eixo_y=eixo_y)

    script = TEMPLATE_STREAMLIT.format(
        titulo=titulo,
        dados_json=dados_json,
        eixo_x=eixo_x,
        codigo_grafico=codigo_grafico,
    )

    SCRIPTS_DIRETORIO.mkdir(parents=True, exist_ok=True)
    script_path = SCRIPTS_DIRETORIO / f"app_{int(time.time())}.py"
    script_path.write_text(script, encoding="utf-8")

    porta = encontrar_porta_livre()

    erro_lancamento = lanca_streamlit_destacado(script_path, porta)
    if erro_lancamento:
        return {"ok": False, "error": erro_lancamento, "streamlit_exe": STREAMLIT_EXE}

    if not aguarda_porta(porta, timeout=25):
        return {"ok": False, "error": f"O servidor não respondeu na porta {porta} dentro do tempo limite."}

    host = "localhost" if ENDERECO_STREAMLIT != "0.0.0.0" else ENDERECO_STREAMLIT
    url = f"http://{host}:{porta}"
    return {"ok": True, "url": url, "script_path": str(script_path)}


if __name__ == "__main__":
    mcp.run()
