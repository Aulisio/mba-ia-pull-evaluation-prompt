"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure


PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


class TestPrompts:
    @pytest.fixture(autouse=True)
    def load_prompt(self):
        data = load_prompts(str(PROMPT_PATH))
        assert isinstance(data, dict) and "bug_to_user_story_v2" in data
        self.prompt = data["bug_to_user_story_v2"]

    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert self.prompt.get("system_prompt", "").strip()

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        assert "Você é um Product Manager" in self.prompt["system_prompt"]

    def test_prompt_mentions_format(self):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = self.prompt["system_prompt"]
        assert "Markdown" in system_prompt
        assert "Como [ator]" in system_prompt
        assert "Critérios de Aceitação" in system_prompt

    def test_prompt_has_few_shot_examples(self):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = self.prompt["system_prompt"]
        assert system_prompt.count("Entrada:") >= 2
        assert system_prompt.count("Saída:") >= 2

    def test_prompt_no_todos(self):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        prompt_text = yaml.safe_dump(self.prompt, allow_unicode=True)
        assert "[TODO]" not in prompt_text

    def test_minimum_techniques(self):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        assert len(self.prompt.get("techniques_applied", [])) >= 2

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])