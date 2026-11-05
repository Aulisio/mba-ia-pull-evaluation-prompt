"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

DICAS DE IMPLEMENTAÇÃO:

- O push é feito pelo cliente do LangSmith:

      from langsmith import Client
      from langchain_core.prompts import ChatPromptTemplate

      client = Client()
      prompt = ChatPromptTemplate.from_messages([
          ("system", system_prompt),
          ("user", user_prompt),
      ])
      url = client.push_prompt(
          f"{username}/bug_to_user_story_v2",
          object=prompt,
          is_public=True,
          description="...",
          tags=[...],
      )

- `username` vem de USERNAME_LANGSMITH_HUB no .env e precisa ser o seu handle
  do Hub. Se você ainda não tem um handle, veja as instruções no .env.example.

- A variável do template precisa ser {bug_report}, que é a chave de entrada
  usada no dataset de avaliação.

- Use `load_yaml` de utils.py para ler o arquivo .yml.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return False

    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_data["system_prompt"]),
            ("user", prompt_data["user_prompt"]),
        ])
        if "bug_report" not in prompt.input_variables:
            print("❌ O template precisa declarar a variável {bug_report}.")
            return False

        techniques = prompt_data["techniques_applied"]
        description = prompt_data["description"]
        readme = (
            f"{description}\n\n"
            f"Versão: {prompt_data['version']}\n\n"
            "Técnicas aplicadas:\n"
            + "\n".join(f"- {technique}" for technique in techniques)
        )

        client = Client()
        url = client.push_prompt(
            prompt_name,
            object=prompt,
            is_public=True,
            description=description,
            readme=readme,
            tags=prompt_data.get("tags", []) + techniques,
        )
        print(f"✓ Prompt publicado publicamente: {prompt_name}")
        print(f"✓ URL: {url}")
        return True
    except Exception as error:
        print(f"❌ Falha ao publicar o prompt: {error}")
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []
    if not isinstance(prompt_data, dict):
        return False, ["O conteúdo do prompt deve ser um objeto YAML."]

    for field in ("description", "version", "system_prompt", "user_prompt"):
        if not isinstance(prompt_data.get(field), str) or not prompt_data[field].strip():
            errors.append(f"Campo obrigatório ausente ou vazio: {field}")

    techniques = prompt_data.get("techniques_applied", [])
    if not isinstance(techniques, list) or len(techniques) < 2:
        errors.append("O prompt deve listar pelo menos duas técnicas em techniques_applied.")

    if "[TODO]" in str(prompt_data):
        errors.append("O prompt ainda contém [TODO].")

    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_data.get("system_prompt", "")),
            ("user", prompt_data.get("user_prompt", "")),
        ])
        if "bug_report" not in prompt.input_variables:
            errors.append("O template precisa declarar a variável {bug_report}.")
    except Exception as error:
        errors.append(f"Não foi possível montar o template LangChain: {error}")

    return not errors, errors


def main():
    """Função principal"""
    print_section_header("Push público do prompt otimizado para o LangSmith")
    required_vars = ["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]
    if not check_env_vars(required_vars):
        return 1

    username = os.environ["USERNAME_LANGSMITH_HUB"].strip()
    if "/" in username:
        print(
            "❌ USERNAME_LANGSMITH_HUB deve conter somente o handle público, "
            "sem '/' nem o nome do prompt. Exemplo: meu-handle."
        )
        return 1

    prompt_file = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
    prompt_document = load_yaml(str(prompt_file))
    if not prompt_document:
        return 1

    prompt_name = f"{username}/bug_to_user_story_v2"
    prompt_data = prompt_document.get("bug_to_user_story_v2")
    if not prompt_data:
        print("❌ O YAML não contém a chave bug_to_user_story_v2.")
        return 1

    return 0 if push_prompt_to_langsmith(prompt_name, prompt_data) else 1


if __name__ == "__main__":
    sys.exit(main())
