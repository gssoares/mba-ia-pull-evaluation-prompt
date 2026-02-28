"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


def pull_prompts_from_langsmith():
    """
    Faz pull dos prompts do LangSmith Hub.

    Returns:
        dict: Dicionário com os prompts baixados ou None se erro
    """
    prompts_to_pull = [
        "leonanluppi/bug_to_user_story_v1"
    ]
    
    pulled_prompts = {}
    
    for prompt_repo in prompts_to_pull:
        try:
            print(f"📥 Fazendo pull do prompt: {prompt_repo}")
            
            # Pull do prompt do hub
            prompt_template = hub.pull(prompt_repo)
            
            # Extrair informações do template
            prompt_name = prompt_repo.split('/')[-1]  # Pega apenas o nome após a '/'
            
            # Construir estrutura do prompt
            prompt_data = {
                "description": f"Prompt para converter relatos de bugs em User Stories",
                "system_prompt": "",
                "user_prompt": "{bug_report}",
                "version": "v1",
                "created_at": "2025-01-15",
                "tags": ["bug-analysis", "user-story", "product-management"]
            }
            
            # Extrair mensagens do ChatPromptTemplate
            if hasattr(prompt_template, 'messages'):
                for message in prompt_template.messages:
                    if hasattr(message, 'type') and hasattr(message, 'content'):
                        if message.type == 'system':
                            prompt_data["system_prompt"] = message.content
                        elif message.type == 'human' or message.type == 'user':
                            prompt_data["user_prompt"] = message.content
            
            # Se não conseguiu extrair system_prompt, usar um padrão baseado no formato string
            if not prompt_data["system_prompt"] and hasattr(prompt_template, 'template'):
                # Se for um PromptTemplate simples
                prompt_data["system_prompt"] = prompt_template.template
                prompt_data["user_prompt"] = "{bug_report}"
            elif not prompt_data["system_prompt"]:
                # Fallback para prompt básico
                prompt_data["system_prompt"] = (
                    "Você é um assistente que ajuda a transformar relatos de bugs de usuários em tarefas para desenvolvedores.\n\n"
                    "Analise o relato de bug abaixo e crie uma user story a partir dele.\n\n"
                    "Relato de Bug:\n---\n{bug_report}\n---\n\nUser Story gerada:"
                )
            
            pulled_prompts[prompt_name] = prompt_data
            
            print(f"✅ Prompt '{prompt_name}' baixado com sucesso!")
            print(f"📋 Descrição: {prompt_data['description']}")
            print(f"📏 Tamanho do system_prompt: {len(prompt_data['system_prompt'])} caracteres")
            
        except Exception as e:
            print(f"❌ Erro ao fazer pull do prompt '{prompt_repo}': {str(e)}")
            print(f"🔍 Verifique se o prompt existe e suas credenciais estão corretas.")
            continue
    
    return pulled_prompts if pulled_prompts else None


def main():
    """Função principal"""
    print_section_header("📥 PULL de Prompts do LangSmith Hub")
    
    # 1. Verificar variáveis de ambiente
    required_vars = ['LANGSMITH_API_KEY']
    
    if not check_env_vars(required_vars):
        return 1
    
    # 2. Fazer pull dos prompts
    print("🔗 Conectando ao LangSmith Hub...")
    
    prompts_data = pull_prompts_from_langsmith()
    
    if not prompts_data:
        print("❌ Nenhum prompt foi baixado com sucesso.")
        return 1
    
    # 3. Salvar prompts localmente
    output_file = "prompts/raw_prompts.yml"
    
    print(f"\n💾 Salvando prompts em: {output_file}")
    
    # Garantir que o diretório existe
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    if save_yaml(prompts_data, output_file):
        print(f"✅ Prompts salvos com sucesso em: {output_file}")
        
        # 4. Mostrar resumo
        print_section_header("📊 RESUMO")
        print(f"📁 Arquivo gerado: {output_file}")
        print(f"📋 Prompts baixados: {len(prompts_data)}")
        
        for prompt_name in prompts_data.keys():
            print(f"   • {prompt_name}")
        
        print("\n📋 PRÓXIMOS PASSOS:")
        print("   1. Analise os prompts em prompts/raw_prompts.yml")
        print("   2. Crie sua versão otimizada em prompts/bug_to_user_story_v2.yml")
        print("   3. Execute: python src/push_prompts.py")
        print("   4. Execute: python src/evaluate.py")
        
        return 0
    else:
        print(f"❌ Erro ao salvar prompts em: {output_file}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
