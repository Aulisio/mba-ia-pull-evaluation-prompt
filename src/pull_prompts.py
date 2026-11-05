"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt semente do desafio
3. Salva localmente em prompts/bug_to_user_story_v1.yml

DICAS DE IMPLEMENTAÇÃO:

- O pull é feito pelo cliente do LangSmith:

      from langsmith import Client
      client = Client()
      prompt = client.pull_prompt(
          "leonanluppi/bug_to_user_story_v1",
          dangerously_pull_public_prompt=True,
      )

- O parâmetro `dangerously_pull_public_prompt=True` é obrigatório sempre que o
  identificador tem dono explícito ("owner/nome"). O LangSmith bloqueia esse pull
  por padrão porque um prompt do Hub é um objeto LangChain serializado, que pode
  vir de terceiros. Aqui o prompt é o do desafio, então o risco é conhecido.

- O retorno é um ChatPromptTemplate. Para extrair o conteúdo das mensagens,
  use a serialização nativa do LangChain (`prompt.messages`, e o atributo
  `.prompt.template` de cada mensagem).

- Use `save_yaml` de utils.py para gravar o resultado no arquivo .yml.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts.chat import HumanMessagePromptTemplate, SystemMessagePromptTemplate
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


def pull_prompts_from_langsmith():
    prompt_name = "leonanluppi/bug_to_user_story_v1"
    output_path = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v1.yml"

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return False

    try:
        client = Client()
        prompt = client.pull_prompt(
            prompt_name,
            dangerously_pull_public_prompt=True,
        )

        prompt_data = {
            "description": "Prompt original para converter relatos de bugs em User Stories",
            "version": "v1",
            "system_prompt": "",
            "user_prompt": "",
            "tags": ["bug-analysis", "user-story", "product-management"],
        }

        for message in prompt.messages:
            message_prompt = getattr(message, "prompt", None)
            template = getattr(message_prompt, "template", None)
            if template is None:
                template = getattr(message, "content", "")

            if isinstance(message, SystemMessagePromptTemplate):
                prompt_data["system_prompt"] = template
            elif isinstance(message, HumanMessagePromptTemplate):
                prompt_data["user_prompt"] = template

        if not prompt_data["system_prompt"] and not prompt_data["user_prompt"]:
            raise ValueError("O prompt remoto não contém mensagens system/user reconhecíveis.")

        if not save_yaml({"bug_to_user_story_v1": prompt_data}, str(output_path)):
            return False

        print(f"✓ Prompt baixado de {prompt_name}")
        print(f"✓ Arquivo salvo em {output_path}")
        return True
    except Exception as error:
        print(f"❌ Não foi possível fazer pull do prompt: {error}")
        return False


def main():
    """Função principal"""
    print_section_header("Pull do prompt inicial do LangSmith")
    return 0 if pull_prompts_from_langsmith() else 1


if __name__ == "__main__":
    sys.exit(main())
