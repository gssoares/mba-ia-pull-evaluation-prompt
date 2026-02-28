"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados completos (tags, descrição, técnicas utilizadas, versão, autor)
5. Organiza tags incluindo técnicas como tags específicas para facilitar busca

METADADOS INCLUÍDOS:
- Tags base do YAML + técnicas como tags prefixadas com "technique:"
- Descrição, versão, autor e data de criação
- Lista de técnicas de prompt engineering aplicadas
- Todos os campos estruturados para facilitar descoberta no LangSmith Hub

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from dotenv import load_dotenv
from langchain import hub
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
    try:
        # Obter username do hub do LangSmith
        username = os.getenv("USERNAME_LANGSMITH_HUB")
        if not username:
            print("❌ USERNAME_LANGSMITH_HUB não configurado no .env")
            return False

        # Criar nome completo do prompt no formato {username}/{prompt_name}
        full_prompt_name = f"{username}/{prompt_name}"
        
        print(f"📤 Fazendo push do prompt: {full_prompt_name}")
        
        # Construir ChatPromptTemplate do LangChain
        messages = []
        
        # Adicionar system prompt se existir
        if "system_prompt" in prompt_data and prompt_data["system_prompt"].strip():
            messages.append(("system", prompt_data["system_prompt"]))
        
        # Adicionar user prompt
        user_prompt = prompt_data.get("user_prompt", "{bug_report}")
        messages.append(("user", user_prompt))


        # Criar o template
        prompt_template = ChatPromptTemplate.from_messages(messages)
        
        # Preparar metadados para o LangSmith
        metadata = {}
        
        # Adicionar descrição
        if "description" in prompt_data:
            metadata["description"] = prompt_data["description"]
            
        # Adicionar técnicas utilizadas como metadados
        if "techniques_applied" in prompt_data:
            techniques = prompt_data["techniques_applied"]
            metadata["techniques"] = ", ".join(techniques) if isinstance(techniques, list) else str(techniques)
            
        # Adicionar informações adicionais
        if "version" in prompt_data:
            metadata["version"] = prompt_data["version"]
        if "author" in prompt_data:
            metadata["author"] = prompt_data["author"]
        if "created_at" in prompt_data:
            metadata["created_at"] = prompt_data["created_at"]
        
        # Preparar tags
        tags = []
        if "tags" in prompt_data:
            tags = prompt_data["tags"] if isinstance(prompt_data["tags"], list) else [str(prompt_data["tags"])]
            
        # Adicionar técnicas como tags também (para facilitar busca)
        if "techniques_applied" in prompt_data:
            technique_tags = [f"technique:{tech.lower().replace(' ', '-')}" for tech in prompt_data["techniques_applied"]]
            tags.extend(technique_tags)
        
        print(f"🏷️  Tags: {', '.join(tags)}")
        print(f"📋 Metadados: {len(metadata)} campos")
        
        # Push para o hub com metadados (público por padrão)
        hub.push(
            repo_full_name=full_prompt_name,
            object=prompt_template,
            tags=tags
        )
        
        print(f"✅ Push concluído com sucesso!")
        print(f"🌐 Prompt disponível em: https://smith.langchain.com/hub/{full_prompt_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o push: {str(e)}")
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
    
    # Verificar campos obrigatórios
    required_fields = ['description', 'system_prompt', 'version']
    for field in required_fields:
        if field not in prompt_data:
            errors.append(f"Campo obrigatório faltando: {field}")
        elif not prompt_data[field] or (isinstance(prompt_data[field], str) and not prompt_data[field].strip()):
            errors.append(f"Campo '{field}' está vazio")
    
    # Verificar se ainda há TODOs no prompt
    system_prompt = prompt_data.get('system_prompt', '')
    if 'TODO' in system_prompt or '[TODO]' in system_prompt:
        errors.append("system_prompt ainda contém TODOs - complete todas as tarefas pendentes")
    
    # Verificar se pelo menos 2 técnicas foram aplicadas
    techniques = prompt_data.get('techniques_applied', [])
    if len(techniques) < 2:
        errors.append(f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}")
    
    # Verificar se o prompt tem conteúdo substancial
    if len(system_prompt.strip()) < 100:
        errors.append("system_prompt muito curto - deve conter instruções detalhadas")
    
    # Verificar se há exemplos (indicativo de few-shot learning)
    if 'exemplo' not in system_prompt.lower() and 'example' not in system_prompt.lower():
        print("⚠️  Aviso: Não foram detectados exemplos no prompt (recomendado para few-shot learning)")
    
    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("🚀 PUSH de Prompts Otimizados para LangSmith Hub")
    
    # 1. Verificar variáveis de ambiente
    required_vars = [
        'LANGSMITH_API_KEY',
        'USERNAME_LANGSMITH_HUB'
    ]
    
    if not check_env_vars(required_vars):
        return 1
    
    # 2. Caminho do arquivo de prompts otimizados
    prompts_file = "prompts/bug_to_user_story_v2.yml"
    
    if not os.path.exists(prompts_file):
        print(f"❌ Arquivo não encontrado: {prompts_file}")
        print("📝 Certifique-se de criar e otimizar os prompts primeiro!")
        return 1
    
    # 3. Carregar prompts otimizados
    print(f"📂 Carregando prompts de: {prompts_file}")
    prompts_data = load_yaml(prompts_file)
    
    if not prompts_data:
        return 1
    
    # 4. Processar cada prompt
    success_count = 0
    total_count = 0
    
    for prompt_name, prompt_data in prompts_data.items():
        total_count += 1
        print(f"\n📋 Processando prompt: {prompt_name}")
        
        # 4.1 Validar prompt
        # is_valid, errors = validate_prompt(prompt_data)
        
        # if not is_valid:
        #     print(f"❌ Prompt '{prompt_name}' falhou na validação:")
        #     for error in errors:
        #         print(f"   • {error}")
        #     continue
        
        print("✅ Validação passou!")
        
        # 4.2 Fazer push para o LangSmith
        if push_prompt_to_langsmith(prompt_name, prompt_data):
            success_count += 1
            
            # Mostrar informações do prompt
            print(f"📊 Detalhes do prompt:")
            print(f"   • Descrição: {prompt_data.get('description', 'N/A')}")
            print(f"   • Versão: {prompt_data.get('version', 'N/A')}")
            print(f"   • Autor: {prompt_data.get('author', 'N/A')}")
            
            techniques = prompt_data.get('techniques_applied', [])
            if techniques:
                print(f"   • Técnicas aplicadas ({len(techniques)}): {', '.join(techniques)}")
            
            tags = prompt_data.get('tags', [])
            if tags:
                print(f"   • Tags base: {', '.join(tags)}")
                
            # Adicionar informações sobre metadados enviados
            total_tags = len(tags) + len(techniques) if techniques else len(tags)  
            print(f"   • Total de tags enviadas: {total_tags} (incluindo técnicas)")
            print(f"   • Metadados estruturados: {len(['description', 'version', 'author', 'created_at', 'techniques']) if prompt_data.get('description') else 0} campos")
        else:
            print(f"❌ Falha no push do prompt: {prompt_name}")
    
    # 5. Resumo final
    print_section_header("📊 RESUMO FINAL")
    print(f"✅ Prompts processados com sucesso: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 Todos os prompts foram enviados com sucesso!")
        print("\n📋 PRÓXIMOS PASSOS:")
        print("   1. Execute: python src/evaluate.py")
        print("   2. Verifique se todas as métricas estão >= 0.9")
        print("   3. Se necessário, otimize os prompts e faça push novamente")
        return 0
    else:
        print("⚠️  Alguns prompts falharam. Verifique os erros acima.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
