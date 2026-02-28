"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
import re
from pathlib import Path
from typing import Dict, Any

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

class TestPrompts:
    """Classe de testes para validação de prompts."""
    
    @pytest.fixture(autouse=True)
    def setup_prompts(self):
        """Setup para carregar os prompts antes de cada teste."""
        prompts_dir = Path(__file__).parent.parent / "prompts"
        self.prompt_files = [
            prompts_dir / "bug_to_user_story_v2.yml"
        ]
        self.all_prompts = {}
        
        for file_path in self.prompt_files:
            if file_path.exists():
                prompts_data = load_prompts(file_path)
                self.all_prompts.update(prompts_data)
    
    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        for prompt_name, prompt_data in self.all_prompts.items():
            assert 'system_prompt' in prompt_data, f"Prompt '{prompt_name}' não possui campo 'system_prompt'"
            assert prompt_data['system_prompt'], f"Campo 'system_prompt' está vazio no prompt '{prompt_name}'"
            assert prompt_data['system_prompt'].strip(), f"Campo 'system_prompt' contém apenas espaços no prompt '{prompt_name}'"

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        role_patterns = [
            r'Você é um\(a?\)\s+\w+',
            r'Você é um\(a?\)\s+\w+\s+\w+',
            r'Atue como\s+\w+',
            r'Como\s+\w+',
            r'Assuma o papel de\s+\w+'
        ]
        
        for prompt_name, prompt_data in self.all_prompts.items():
            system_prompt = prompt_data.get('system_prompt', '')
            has_role = any(re.search(pattern, system_prompt, re.IGNORECASE) for pattern in role_patterns)
            assert has_role, f"Prompt '{prompt_name}' não define uma persona clara (ex: 'Você é um Product Manager')"

    def test_prompt_mentions_format(self):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        format_keywords = [
            'markdown', 'user story', 'formato', 'estrutura', 'template',
            'padrão', 'modelo', 'layout', 'formatação'
        ]
        
        for prompt_name, prompt_data in self.all_prompts.items():
            system_prompt = prompt_data.get('system_prompt', '').lower()
            description = prompt_data.get('description', '').lower()
            full_prompt = system_prompt + ' ' + description
            
            mentions_format = any(keyword in full_prompt for keyword in format_keywords)
            assert mentions_format, f"Prompt '{prompt_name}' não menciona formato específico (Markdown, User Story, etc.)"

    def test_prompt_has_few_shot_examples(self):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        example_patterns = [
            r'exemplo\s*\d*:',
            r'## exemplo',
            r'# exemplo',
            r'**exemplo',
            r'bug report:.*user story',
            r'entrada:.*saída:',
            r'input:.*output:'
        ]
        
        for prompt_name, prompt_data in self.all_prompts.items():
            system_prompt = prompt_data.get('system_prompt', '')
            
            has_examples = any(re.search(pattern, system_prompt, re.IGNORECASE | re.DOTALL) 
                             for pattern in example_patterns)
            
            # Verifica também se há seções que parecem exemplos estruturados
            example_sections = system_prompt.count('**') >= 4  # Pelo menos 2 pares de **
            has_structured_examples = '###' in system_prompt or example_sections
            
            assert has_examples or has_structured_examples, f"Prompt '{prompt_name}' não contém exemplos few-shot estruturados"

    def test_prompt_no_todos(self):
        """Garante que você não esqueceu nenhum [TODO] no texto."""
        todo_patterns = [
            r'\[todo\]',
            r'\[TODO\]',
            r'TODO:',
            r'todo:',
            r'FIXME',
            r'XXX'
        ]
        
        for prompt_name, prompt_data in self.all_prompts.items():
            # Verifica em todos os campos de texto do prompt
            text_fields = ['system_prompt', 'user_prompt', 'description']
            
            for field in text_fields:
                if field in prompt_data:
                    field_content = str(prompt_data[field])
                    for pattern in todo_patterns:
                        matches = re.findall(pattern, field_content, re.IGNORECASE)
                        assert not matches, f"Prompt '{prompt_name}' contém TODOs pendentes no campo '{field}': {matches}"

    def test_minimum_techniques(self):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        for prompt_name, prompt_data in self.all_prompts.items():
            techniques_applied = prompt_data.get('techniques_applied', [])
            
            # Se não há campo techniques_applied, verifica se é um prompt mais básico (v1)
            if not techniques_applied:
                # Para prompts v1, pode não ter techniques_applied, mas devemos incentivar a evolução
                version = prompt_data.get('version', '')
                if version == 'v1':
                    # Para v1, aceita que não tenha técnicas listadas, mas emite aviso
                    pass
                else:
                    assert False, f"Prompt '{prompt_name}' não possui metadados 'techniques_applied'"
            else:
                assert len(techniques_applied) >= 2, f"Prompt '{prompt_name}' deveria aplicar pelo menos 2 técnicas, mas aplicou apenas {len(techniques_applied)}: {techniques_applied}"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])