from pathlib import Path
from src.schemas import AgentState

SKILLS_DIR = Path(__file__).resolve().parents[2] / "src" / "skills"

def skill_loader_node(state: AgentState) -> dict:
    """Lê o catálogo de skills e injeta a lista no estado"""

    linhas = []
    nomes_carregados = []

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        conteudo = skill_md.read_text(encoding="utf-8")
        nome = skill_dir.name
        descricao = ""
        for linha in conteudo.splitlines():
            if linha.startswith("description:"):
                descricao = linha.replace("description:", "").strip()
                break
        linhas.append(f"{nome}: {descricao} -> {skill_md}")
        nomes_carregados.append(nome)

    available_skills = "\n".join(linhas)
    return {"active_skills": nomes_carregados, "skill_catalog": available_skills}
