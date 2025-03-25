"""
External LLM advisor for code improvements using various AI models.
"""
import os
import json
import time
import requests
from typing import Dict, List, Any
from urllib.parse import urljoin
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMAdvisor:
    """Class to request code improvement suggestions from external LLMs"""
    
    def __init__(self, config_path=None):
        """Initialize with optional config file path"""
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'data', 'advisor_config.json'
        )
        self.config = self.load_config()
        self.providers = {
            "openai": self.query_openai,
            "deepseek": self.query_deepseek,
            "anthropic": self.query_anthropic,
            "local": self.query_local_llm,
        }
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        # Default configuration
        config = {
            "default_provider": "local",
            "providers": {
                "openai": {
                    "api_key": "",
                    "model": "gpt-4",
                    "api_base": "https://api.openai.com/v1",
                    "enabled": False
                },
                "deepseek": {
                    "api_key": "",
                    "model": "deepseek-coder-33b-instruct",
                    "api_base": "https://api.deepseek.com/v1",
                    "enabled": False
                },
                "anthropic": {
                    "api_key": "",
                    "model": "claude-3-opus-20240229",
                    "api_base": "https://api.anthropic.com/v1/messages",
                    "enabled": False
                },
                "local": {
                    "api_base": "http://127.0.0.1:8000/v1",
                    "model": "local-model",
                    "enabled": True
                }
            },
            "prompts": {
                "code_review": "You are an expert programmer tasked with improving the following code. Please suggest improvements for clarity, efficiency, security, and best practices. Focus on specific, actionable suggestions that will make the code better.\n\nCode to review:\n```{language}\n{code}\n```\n\nPlease provide your suggestions in a clear, numbered list format with brief explanations.",
                "bug_fixing": "You are a debugging expert. Review this code and identify any potential bugs or issues:\n\n```{language}\n{code}\n```\n\nPlease list all potential bugs or issues you find and suggest fixes for each one.",
                "algorithm_optimization": "You are an algorithm optimization specialist. Review the following code and suggest optimizations to improve its time/space complexity:\n\n```{language}\n{code}\n```\n\nPlease analyze the algorithm, identify its current complexity, and suggest specific optimizations."
            }
        }
        
        # Save default config
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        return config
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def set_api_key(self, provider: str, api_key: str) -> bool:
        """Set API key for a specific provider"""
        if provider in self.config["providers"]:
            self.config["providers"][provider]["api_key"] = api_key
            self.config["providers"][provider]["enabled"] = bool(api_key)
            self.save_config()
            return True
        return False
    
    def get_enabled_providers(self) -> List[str]:
        """Get list of enabled providers"""
        return [p for p, details in self.config["providers"].items() if details.get("enabled", False)]

    def get_default_provider(self) -> str:
        """Get the current default provider"""
        return self.config.get("default_provider", "local")
    
    def set_default_provider(self, provider: str) -> bool:
        """Set the default provider"""
        if provider in self.config["providers"] and self.config["providers"][provider].get("enabled", False):
            self.config["default_provider"] = provider
            self.save_config()
            return True
        return False
    
    def get_language_from_filename(self, filename: str) -> str:
        """Detect programming language from file extension"""
        ext = os.path.splitext(filename)[1].lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.java': 'java',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.r': 'r',
            '.jl': 'julia',
            '.sh': 'bash',
            '.bat': 'batch',
            '.ps1': 'powershell',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css'
        }
        return language_map.get(ext, 'text')
    
    def get_advice(self, code: str, file_path: str = None, prompt_type: str = "code_review", 
                  provider: str = None, timeout: int = 60) -> Dict[str, Any]:
        """Get advice from the specified LLM provider"""
        if not code:
            return {"success": False, "error": "No code provided", "suggestions": []}
        
        # Determine provider to use
        provider = provider or self.get_default_provider()
        if provider not in self.providers or not self.config["providers"].get(provider, {}).get("enabled", False):
            available = self.get_enabled_providers()
            if not available:
                return {"success": False, "error": "No LLM providers are enabled", "suggestions": []}
            provider = available[0]
        
        # Format prompt with code
        language = "python"  # Default language
        if file_path:
            language = self.get_language_from_filename(file_path)
        
        prompt_template = self.config["prompts"].get(prompt_type, self.config["prompts"]["code_review"])
        prompt = prompt_template.format(language=language, code=code)
        
        try:
            # Call appropriate provider function
            provider_func = self.providers.get(provider)
            if not provider_func:
                return {"success": False, "error": f"Provider {provider} not supported", "suggestions": []}
            
            # Track time
            start_time = time.time()
            response_text = provider_func(prompt)
            elapsed = time.time() - start_time
            
            # Parse suggestions from response
            suggestions = self.parse_suggestions(response_text)
            
            return {
                "success": True,
                "provider": provider,
                "elapsed_time": elapsed,
                "timestamp": time.time(),
                "file_path": file_path,
                "prompt_type": prompt_type,
                "response": response_text,
                "suggestions": suggestions
            }
        except Exception as e:
            logger.error(f"Error getting advice from {provider}: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": provider,
                "suggestions": [],
                "timestamp": time.time(),
                "file_path": file_path,
                "prompt_type": prompt_type
            }
    
    def parse_suggestions(self, text: str) -> List[Dict[str, Any]]:
        """Parse suggestions from LLM response text into structured format"""
        suggestions = []
        # Split by numbered items (1. 2. 3. etc) and try to parse each one
        import re
        numbered_items = re.split(r'\n\s*\d+\.', '\n' + text)
        if len(numbered_items) > 1:  # Found numbered list
            for i, item in enumerate(numbered_items[1:]):  # Skip first element which is empty or intro
                item = item.strip()
                if not item:
                    continue
                suggestion = {
                    "id": i + 1,
                    "text": item,
                    "confidence": 0.9,  # Default confidence
                    "type": "improvement"
                }
                # Try to detect suggestion type
                if "bug" in item.lower() or "fix" in item.lower() or "error" in item.lower():
                    suggestion["type"] = "bug_fix"
                elif "efficien" in item.lower() or "performance" in item.lower() or "optimiz" in item.lower():
                    suggestion["type"] = "optimization"
                elif "readab" in item.lower() or "naming" in item.lower() or "comment" in item.lower():
                    suggestion["type"] = "readability"
                suggestions.append(suggestion)
        else:
            # No clear numbered list, just return the text as one suggestion
            suggestions.append({
                "id": 1,
                "text": text.strip(),
                "confidence": 0.7,
                "type": "general_advice"
            })
        
        return suggestions
    
    def query_local_llm(self, prompt: str) -> str:
        """Query the local LLM server"""
        try:
            config = self.config["providers"]["local"]
            api_base = config["api_base"]
            
            # Try OpenAI-compatible chat endpoint first
            headers = {"Content-Type": "application/json"}
            data = {
                "model": config.get("model", "local-model"),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            try:
                response = requests.post(
                    urljoin(api_base, "/chat/completions"), 
                    headers=headers,
                    json=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        if "message" in result["choices"][0]:
                            return result["choices"][0]["message"].get("content", "")
            except Exception as chat_error:
                logger.debug(f"Chat completions failed: {chat_error}, trying completion endpoint")
            
            # Fallback to completion endpoint
            data = {
                "prompt": prompt,
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            response = requests.post(
                urljoin(api_base, "/completions"), 
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0].get("text", "")
            
            # Try one more time with a simplified approach
            data = {"prompt": prompt}
            try:
                response = requests.post(api_base, json=data, timeout=60)
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", result.get("output", ""))
            except Exception:
                pass
                
            raise Exception(f"Local LLM request failed: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Error querying local LLM: {e}")
            raise
    
    def query_openai(self, prompt: str) -> str:
        """Query OpenAI API for code improvement suggestions"""
        config = self.config["providers"]["openai"]
        if not config.get("api_key"):
            raise Exception("OpenAI API key not configured")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}"
        }
        
        # Modern Chat API format
        data = {
            "model": config.get("model", "gpt-4"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        response = requests.post(
            urljoin(config["api_base"], "/chat/completions"),
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        
        raise Exception(f"OpenAI request failed: {response.status_code} - {response.text}")
    
    def query_deepseek(self, prompt: str) -> str:
        """Query DeepSeek API for code improvement suggestions"""
        config = self.config["providers"]["deepseek"]
        if not config.get("api_key"):
            raise Exception("DeepSeek API key not configured")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}"
        }
        
        # DeepSeek uses OpenAI-compatible API
        data = {
            "model": config.get("model", "deepseek-coder-33b-instruct"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 2000
        }
        
        response = requests.post(
            urljoin(config["api_base"], "/chat/completions"),
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        
        raise Exception(f"DeepSeek request failed: {response.status_code} - {response.text}")
    
    def query_anthropic(self, prompt: str) -> str:
        """Query Anthropic API for code improvement suggestions"""
        config = self.config["providers"]["anthropic"]
        if not config.get("api_key"):
            raise Exception("Anthropic API key not configured")
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": config["api_key"],
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": config.get("model", "claude-3-opus-20240229"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 2000
        }
        
        response = requests.post(
            config["api_base"],
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("content", [])
            if content and len(content) > 0:
                return content[0].get("text", "")
            return ""
        
        raise Exception(f"Anthropic request failed: {response.status_code} - {response.text}")
    
    def get_suggestions(self, code: str, file_path: str = None, prompt_type: str = "code_review") -> Dict[str, Any]:
        """Get code improvement suggestions from the configured LLM provider"""
        return self.get_advice(code, file_path=file_path, prompt_type=prompt_type)

# Helper function to compare suggestions from multiple providers
def compare_suggestions(code: str, file_path: str = None, providers: List[str] = None) -> Dict[str, Any]:
    """
    Get and compare suggestions from multiple LLM providers
    
    Returns:
        Dictionary with results from each provider and a combined analysis
    """
    advisor = LLMAdvisor()
    results = {}
    
    # If no providers specified, use all enabled providers
    if not providers:
        providers = advisor.get_enabled_providers()
    
    # Get suggestions from each provider
    for provider in providers:
        result = advisor.get_advice(code, file_path=file_path, provider=provider)
        results[provider] = result
    
    # Analyze combined results (simple implementation for now)
    combined = {
        "providers_consulted": providers,
        "success_count": sum(1 for p in providers if results.get(p, {}).get("success", False)),
        "total_suggestions": sum(len(results.get(p, {}).get("suggestions", [])) for p in providers),
        "common_themes": [],  # Would require NLP to properly identify
        "all_suggestions": []
    }
    
    # Combine all suggestions
    for provider, result in results.items():
        for suggestion in result.get("suggestions", []):
            suggestion["provider"] = provider
            combined["all_suggestions"].append(suggestion)
    
    return {
        "provider_results": results,
        "combined": combined
    }