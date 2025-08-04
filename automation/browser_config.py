"""
Optimized browser configuration for betslip conversion automation.
Contains performance-tuned settings for different use cases.
"""

import os
from typing import Dict, List, Any


class BrowserConfig:
    """Centralized browser configuration management."""
    
    # Base Chrome arguments for all browser instances
    BASE_ARGS = [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-extensions",
        "--disable-plugins",
        "--disable-images",  # Skip images for faster loading
        "--disable-css",     # Skip CSS for faster loading
        "--disable-javascript-harmony-shipping",
        "--memory-pressure-off",
        "--aggressive-cache-discard",
        "--disable-background-timer-throttling",
        "--disable-renderer-backgrounding",
        "--disable-backgrounding-occluded-windows",
        "--disable-features=TranslateUI",
        "--disable-ipc-flooding-protection",
        "--disable-default-apps",
        "--disable-sync",
        "--disable-web-security",  # For faster cross-origin requests
        "--disable-features=VizDisplayCompositor"
    ]
    
    # Performance-optimized arguments for extraction tasks
    EXTRACTION_ARGS = BASE_ARGS + [
        "--max_old_space_size=512",
        "--disable-background-networking",
        "--disable-client-side-phishing-detection",
        "--disable-component-extensions-with-background-pages",
        "--disable-hang-monitor"
    ]
    
    # Memory-optimized arguments for parallel processing
    PARALLEL_ARGS = BASE_ARGS + [
        "--max_old_space_size=256",
        "--disable-background-networking",
        "--disable-client-side-phishing-detection",
        "--disable-component-extensions-with-background-pages",
        "--disable-hang-monitor",
        "--disable-prompt-on-repost",
        "--disable-domain-reliability"
    ]
    
    # High-performance arguments for betslip creation
    CREATION_ARGS = BASE_ARGS + [
        "--max_old_space_size=768",
        "--disable-background-networking",
        "--disable-client-side-phishing-detection"
    ]
    
    @classmethod
    def get_extraction_config(cls) -> Dict[str, Any]:
        """Get optimized config for betslip extraction tasks."""
        return {
            "headless": True,
            "stealth": True,
            "timeout": 20000,  # 20 seconds for extraction
            "viewport": {"width": 1280, "height": 720},
            "args": cls.EXTRACTION_ARGS
        }
    
    @classmethod
    def get_creation_config(cls) -> Dict[str, Any]:
        """Get optimized config for betslip creation tasks."""
        return {
            "headless": True,
            "stealth": True,
            "timeout": 35000,  # 35 seconds for creation
            "viewport": {"width": 1280, "height": 720},
            "args": cls.CREATION_ARGS
        }
    
    @classmethod
    def get_parallel_config(cls) -> Dict[str, Any]:
        """Get memory-optimized config for parallel processing."""
        return {
            "headless": True,
            "stealth": True,
            "timeout": 25000,  # 25 seconds for parallel tasks
            "viewport": {"width": 1280, "height": 720},
            "args": cls.PARALLEL_ARGS
        }
    
    @classmethod
    def get_custom_config(cls, 
                         timeout: int = 30000,
                         memory_limit: int = 512,
                         enable_images: bool = False,
                         enable_css: bool = False) -> Dict[str, Any]:
        """Get custom browser configuration."""
        args = cls.BASE_ARGS.copy()
        
        # Adjust memory limit
        args = [arg for arg in args if not arg.startswith("--max_old_space_size")]
        args.append(f"--max_old_space_size={memory_limit}")
        
        # Enable images if requested
        if enable_images:
            args = [arg for arg in args if arg != "--disable-images"]
        
        # Enable CSS if requested
        if enable_css:
            args = [arg for arg in args if arg != "--disable-css"]
        
        return {
            "headless": True,
            "stealth": True,
            "timeout": timeout,
            "viewport": {"width": 1280, "height": 720},
            "args": args
        }


class LLMConfig:
    """Optimized LLM configuration for different tasks."""
    
    @classmethod
    def get_extraction_config(cls) -> Dict[str, Any]:
        """Get optimized LLM config for extraction tasks."""
        provider = os.getenv('LLM_PROVIDER', 'openai').lower()
        
        if provider == 'anthropic':
            return {
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.1,
                "max_tokens": 1024,  # Sufficient for extraction data
                "request_timeout": 20,
                "max_retries": 2
            }
        else:  # Default to OpenAI
            return {
                "model": "gpt-4o",
                "temperature": 0.1,
                "max_tokens": 1024,  # Sufficient for extraction data
                "request_timeout": 20,
                "max_retries": 2
            }
    
    @classmethod
    def get_creation_config(cls) -> Dict[str, Any]:
        """Get optimized LLM config for creation tasks."""
        provider = os.getenv('LLM_PROVIDER', 'openai').lower()
        
        if provider == 'anthropic':
            return {
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.1,
                "max_tokens": 2048,  # More tokens for complex creation tasks
                "request_timeout": 30,
                "max_retries": 2
            }
        else:  # Default to OpenAI
            return {
                "model": "gpt-4o",
                "temperature": 0.1,
                "max_tokens": 2048,  # More tokens for complex creation tasks
                "request_timeout": 30,
                "max_retries": 2
            }
    
    @classmethod
    def get_parallel_config(cls) -> Dict[str, Any]:
        """Get optimized LLM config for parallel processing."""
        provider = os.getenv('LLM_PROVIDER', 'openai').lower()
        
        if provider == 'anthropic':
            return {
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.1,
                "max_tokens": 512,  # Minimal tokens for speed
                "request_timeout": 15,
                "max_retries": 1
            }
        else:  # Default to OpenAI
            return {
                "model": "gpt-4o",
                "temperature": 0.1,
                "max_tokens": 512,  # Minimal tokens for speed
                "request_timeout": 15,
                "max_retries": 1
            }


# Environment-based configuration
def get_environment_config() -> Dict[str, Any]:
    """Get configuration based on environment variables."""
    env = os.getenv('ENVIRONMENT', 'development').lower()
    
    if env == 'production':
        return {
            'max_concurrent_browsers': int(os.getenv('MAX_CONCURRENT_BROWSERS', '2')),
            'max_memory_mb': int(os.getenv('MAX_MEMORY_MB', '1024')),
            'enable_parallel': os.getenv('ENABLE_PARALLEL', 'true').lower() == 'true',
            'browser_timeout': int(os.getenv('BROWSER_TIMEOUT', '25000')),
            'llm_timeout': int(os.getenv('LLM_TIMEOUT', '20'))
        }
    elif env == 'testing':
        return {
            'max_concurrent_browsers': 1,
            'max_memory_mb': 512,
            'enable_parallel': False,
            'browser_timeout': 15000,
            'llm_timeout': 10
        }
    else:  # development
        return {
            'max_concurrent_browsers': int(os.getenv('MAX_CONCURRENT_BROWSERS', '3')),
            'max_memory_mb': int(os.getenv('MAX_MEMORY_MB', '2048')),
            'enable_parallel': os.getenv('ENABLE_PARALLEL', 'true').lower() == 'true',
            'browser_timeout': int(os.getenv('BROWSER_TIMEOUT', '30000')),
            'llm_timeout': int(os.getenv('LLM_TIMEOUT', '30'))
        }


# Export configuration classes
__all__ = ['BrowserConfig', 'LLMConfig', 'get_environment_config']