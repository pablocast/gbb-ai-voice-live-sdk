"""
Tool configuration loader for Voice Assistant
Loads tool definitions and configurations from YAML files
"""

import os
import yaml
import logging
import importlib
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path

logger = logging.getLogger(__name__)

class ToolConfigLoader:
    """Loads and manages tool configurations from YAML files."""
    
    def __init__(self, config_file: str = "tools_config.yaml"):
        """
        Initialize the tool config loader.
        
        Args:
            config_file: Path to the YAML configuration file
        """
        self.config_file = config_file
        self.config_path = Path(__file__).parent / "tools" / config_file
        self.config = {}
        self.tools = []
        self.environment = os.getenv("ENVIRONMENT", "production")
        
        self._load_config()
        
    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            if not self.config_path.exists():
                logger.error(f"Tool config file not found: {self.config_path}")
                return
                
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)
                logger.info(f"Loaded YAML configuration from {self.config_file}")
                
            # Override environment if specified in config
            if 'default_environment' in self.config:
                default_env = self.config['default_environment']
                if self.environment == "production":  # Only use default if not explicitly set
                    self.environment = default_env
                    
            logger.info(f"Using environment: {self.environment}")
            
        except Exception as e:
            logger.error(f"Error loading tool configuration: {e}")
            self.config = {}
            
    def get_environment_config(self) -> Dict[str, Any]:
        """Get configuration for the current environment."""
        environments = self.config.get('environments', {})
        env_config = environments.get(self.environment, {})
        
        # Set defaults if not specified
        defaults = {
            'enable_all_tools': True,
            'log_function_calls': False,
            'default_timeout_seconds': 10,
            'debug_mode': False
        }
        
        for key, default_value in defaults.items():
            if key not in env_config:
                env_config[key] = default_value
                
        return env_config
        
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions for Azure VoiceLive API.
        
        Returns:
            List of tool definitions ready for the API
        """
        tools = self.config.get('tools', [])
        env_config = self.get_environment_config()
        
        if not env_config.get('enable_all_tools', True):
            logger.info("Tools disabled by environment configuration")
            return []
            
        # Filter enabled tools and format for API
        api_tools = []
        for tool in tools:
            if not tool.get('enabled', True):
                continue
                
            # Create API-compatible tool definition
            api_tool = {
                'type': tool.get('type', 'function'),
                'name': tool.get('name'),
                'description': tool.get('description'),
                'parameters': tool.get('parameters', {})
            }
            
            api_tools.append(api_tool)
            
        logger.info(f"Loaded {len(api_tools)} tool definitions")
        return api_tools
        
    def get_function_implementations(self) -> Dict[str, Callable]:
        """
        Get function implementations by importing them dynamically.
        
        Returns:
            Dictionary mapping function names to callable implementations
        """
        tools = self.config.get('tools', [])
        env_config = self.get_environment_config()
        
        if not env_config.get('enable_all_tools', True):
            return {}
            
        implementations = {}
        
        for tool in tools:
            if not tool.get('enabled', True):
                continue
                
            function_name = tool.get('name')
            impl_config = tool.get('implementation', {})
            
            if not impl_config:
                logger.warning(f"No implementation config for tool: {function_name}")
                continue
                
            module_name = impl_config.get('module')
            function_impl_name = impl_config.get('function')
            
            if not module_name or not function_impl_name:
                logger.warning(f"Incomplete implementation config for tool: {function_name}")
                continue
                
            try:
                # Import the module and get the function
                module = importlib.import_module(module_name)
                func = getattr(module, function_impl_name)
                implementations[function_name] = func
                
                logger.debug(f"Loaded implementation for {function_name} from {module_name}.{function_impl_name}")
                
            except (ImportError, AttributeError) as e:
                logger.error(f"Failed to load implementation for {function_name}: {e}")
                
        logger.info(f"Loaded {len(implementations)} function implementations")
        return implementations
        
    def get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool configuration dictionary
        """
        tools = self.config.get('tools', [])
        for tool in tools:
            if tool.get('name') == tool_name:
                return tool
        return {}
        
    def get_tool_timeout(self, tool_name: str) -> int:
        """
        Get timeout for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Timeout in seconds
        """
        tool_config = self.get_tool_config(tool_name)
        tool_timeout = tool_config.get('timeout_seconds')
        
        if tool_timeout:
            return tool_timeout
            
        # Fall back to environment default
        env_config = self.get_environment_config()
        return env_config.get('default_timeout_seconds', 10)
        
    def is_tool_enabled(self, tool_name: str) -> bool:
        """
        Check if a tool is enabled.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            True if enabled, False otherwise
        """
        env_config = self.get_environment_config()
        if not env_config.get('enable_all_tools', True):
            return False
            
        tool_config = self.get_tool_config(tool_name)
        return tool_config.get('enabled', True)
        
    def should_log_function_calls(self) -> bool:
        """Check if function calls should be logged."""
        env_config = self.get_environment_config()
        return env_config.get('log_function_calls', False)
        
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        env_config = self.get_environment_config()
        return env_config.get('debug_mode', False)
        
    def get_environment_info(self) -> Dict[str, Any]:
        """
        Get information about the current tool environment.
        
        Returns:
            Dictionary with environment information
        """
        env_config = self.get_environment_config()
        tools = self.get_tool_definitions()
        functions = self.get_function_implementations()
        
        return {
            "environment": self.environment,
            "config_file": str(self.config_path),
            "tools_enabled": env_config.get('enable_all_tools', True),
            "tool_count": len(tools),
            "function_count": len(functions),
            "log_function_calls": self.should_log_function_calls(),
            "debug_mode": self.is_debug_mode(),
            "default_timeout": env_config.get('default_timeout_seconds', 10),
        }
        
    def reload(self):
        """Reload configuration from file."""
        self._load_config()
        logger.info("Tool configuration reloaded")

# Global instance
_tool_loader: Optional[ToolConfigLoader] = None

def get_tool_loader(config_file: str = "tools_config.yaml") -> ToolConfigLoader:
    """
    Get the global tool loader instance.
    
    Args:
        config_file: Path to the YAML configuration file
        
    Returns:
        ToolConfigLoader instance
    """
    global _tool_loader
    if _tool_loader is None:
        _tool_loader = ToolConfigLoader(config_file)
    return _tool_loader

def reload_tools():
    """Reload tool configuration."""
    global _tool_loader
    if _tool_loader is not None:
        _tool_loader.reload()
    else:
        _tool_loader = ToolConfigLoader()
    logger.info("Tool configuration reloaded")