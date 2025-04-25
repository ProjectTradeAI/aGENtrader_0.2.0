#!/usr/bin/env python3
"""
LLM Integration for AutoGen

This module provides utilities for integrating local LLMs with AutoGen.
"""
import os
import json
import logging
import datetime
import importlib.util
from typing import Dict, List, Any, Optional, Union, Callable

# Configure logging
logging.basicConfig(level=logging.INFO, 
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("llm_integration")

# Check if AutoGen is available
try:
    import autogen
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    logger.warning("AutoGen is not installed. Some features may not be available.")

# Try to import llama-cpp-python
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    logger.warning("llama-cpp-python is not installed. Local LLM will not be available.")

# Global model instance for reuse
_MODEL_INSTANCE = None

class LocalLLMAPIClient:
    """
    Local LLM API Client for AutoGen integration.
    This class provides a wrapper around local LLM models that's compatible
    with AutoGen's expected client interface.
    """
    
    def __init__(self, model_path: Optional[str] = None, 
                model_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Local LLM API Client.
        
        Args:
            model_path: Path to the model file
            model_config: Configuration for the model
        """
        self.model_path = model_path
        self.model_config = model_config or {}
        self.model = None
        self.logger = logging.getLogger("LocalLLMClient")
        
    def _load_model(self) -> bool:
        """
        Load the model.
        
        Returns:
            True if model loaded successfully, False otherwise
        """
        global _MODEL_INSTANCE
        
        if not LLAMA_CPP_AVAILABLE:
            self.logger.error("llama-cpp-python is not installed. Cannot load local LLM.")
            return False
            
        # If model already loaded globally, use it
        if _MODEL_INSTANCE is not None:
            self.model = _MODEL_INSTANCE
            return True
            
        # Otherwise, load the model
        try:
            # Default to TinyLlama model if available
            if self.model_path is None:
                # Check common locations for TinyLlama model
                potential_paths = [
                    "./models/tinyllama.gguf",
                    "./models/TinyLlama-1.1B-Chat-v1.0.Q5_K_M.gguf",
                    "/models/tinyllama.gguf",
                    "/models/TinyLlama-1.1B-Chat-v1.0.Q5_K_M.gguf",
                    # Add paths found in the system
                    "/home/runner/workspace/models/llm_models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
                    "/home/runner/workspace/.cache/huggingface/hub/models--TheBloke--TinyLlama-1.1B-Chat-v1.0-GGUF/snapshots/52e7645ba7c309695bec7ac98f4f005b139cf465/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
                ]
                
                for path in potential_paths:
                    if os.path.exists(path):
                        self.model_path = path
                        self.logger.info(f"Found TinyLlama model at {path}")
                        break
                        
                if self.model_path is None:
                    self.logger.error("No model path specified and no default model found")
                    return False
            
            # Configure model parameters
            model_params = {
                "n_ctx": 2048,  # Context window size
                "n_threads": min(os.cpu_count() or 4, 4),  # Use up to 4 threads
                "verbose": False,
            }
            
            # Add any additional parameters from model_config
            model_params.update(self.model_config)
            
            self.logger.info(f"Loading model from {self.model_path}")
            self.logger.info(f"Model parameters: {model_params}")
            
            # Load the model
            self.model = Llama(model_path=self.model_path, **model_params)
            
            # Store model globally
            _MODEL_INSTANCE = self.model
            
            self.logger.info("Model loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def completion(self, model: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate a completion with the local model.
        
        This method aligns with the OpenAI API completion interface expected by AutoGen.
        
        Args:
            model: Model name (ignored, using local model)
            prompt: Text prompt for completion
            kwargs: Additional parameters
            
        Returns:
            Completion response in OpenAI-compatible format
        """
        if self.model is None:
            if not self._load_model():
                return {
                    "choices": [{
                        "text": "ERROR: Failed to load the local LLM model.",
                        "finish_reason": "error"
                    }]
                }
        
        # Extract parameters
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 1024)
        stop = kwargs.get("stop", ["</s>", "<|im_end|>", "<|assistant|>", "<|user|>"])
        
        try:
            # Call the model
            self.logger.debug(f"Generating completion for prompt: {prompt}")
            
            response = self.model.create_completion(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop
            )
            
            generated_text = response.get("choices", [{}])[0].get("text", "").strip()
            
            self.logger.debug(f"Generated response: {generated_text}")
            
            # Format the response like OpenAI API
            return {
                "id": f"local-{hash(prompt) % 10000}",
                "object": "text_completion",
                "created": int(datetime.datetime.now().timestamp()),
                "model": "local-llm",
                "choices": [{
                    "text": generated_text,
                    "index": 0,
                    "logprobs": None,
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(prompt) // 4,  # Approximate
                    "completion_tokens": len(generated_text) // 4,  # Approximate
                    "total_tokens": (len(prompt) + len(generated_text)) // 4
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in completion: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
            return {
                "choices": [{
                    "text": f"ERROR: {str(e)}",
                    "finish_reason": "error"
                }]
            }
    
    def chat_completion_create(self, messages: List[Dict[str, str]], 
                            model: str = None, **kwargs) -> Dict[str, Any]:
        """
        Generate a chat completion with the local model.
        
        This method aligns with the OpenAI API chat completion interface expected by AutoGen.
        
        Args:
            messages: List of message dictionaries
            model: Model name (ignored, using local model)
            kwargs: Additional parameters
            
        Returns:
            Chat completion response in OpenAI-compatible format
        """
        if self.model is None:
            if not self._load_model():
                return {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": "ERROR: Failed to load the local LLM model."
                        },
                        "finish_reason": "error"
                    }]
                }
        
        # Process the messages into a prompt
        prompt = self._create_prompt_from_messages(messages)
        
        # Extract parameters
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 1024)
        stop = kwargs.get("stop", ["</s>", "<|im_end|>", "<|assistant|>", "<|user|>"])
        
        try:
            # Generate response
            self.logger.debug(f"Generating chat completion for prompt: {prompt}")
            
            output = self.model.create_completion(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop
            )
            
            # Extract response text
            response_text = output.get("choices", [{}])[0].get("text", "").strip()
            
            self.logger.debug(f"Generated chat response: {response_text}")
            
            # Format response like OpenAI API
            return {
                "id": f"chat-{hash(prompt) % 10000}",
                "object": "chat.completion",
                "created": int(datetime.datetime.now().timestamp()),
                "model": "local-llm",
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": response_text,
                    },
                    "finish_reason": "stop",
                    "index": 0
                }],
                "usage": {
                    "prompt_tokens": len(prompt) // 4,  # Approximate token count
                    "completion_tokens": len(response_text) // 4,
                    "total_tokens": (len(prompt) + len(response_text)) // 4, 
                },
            }
            
        except Exception as e:
            self.logger.error(f"Error in chat completion: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": f"ERROR: {str(e)}"
                    },
                    "finish_reason": "error"
                }]
            }
    
    # Aliasing methods for compatibility with different AutoGen versions
    def create_completion(self, **kwargs):
        """Alias for completion to maintain compatibility"""
        return self.completion(**kwargs)
    
    def create(self, messages=None, prompt=None, **kwargs):
        """Unified create method that handles both chat and completion"""
        if messages:
            return self.chat_completion_create(messages=messages, **kwargs)
        elif prompt:
            return self.completion(prompt=prompt, **kwargs)
        else:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "ERROR: Either messages or prompt must be provided."
                    },
                    "finish_reason": "error"
                }]
            }
        
    def _create_prompt_from_messages(self, messages: List[Dict[str, str]]) -> str:
        """
        Create a prompt string from the messages.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Prompt string
        """
        prompt = ""
        
        # Format for TinyLlama chat model
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                prompt += f"<|system|>\n{content}\n"
            elif role == "user":
                prompt += f"<|user|>\n{content}\n"
            elif role == "assistant":
                prompt += f"<|assistant|>\n{content}\n"
            else:
                prompt += f"{content}\n"
                
        # Add assistant prompt for completion
        prompt += "<|assistant|>\n"
        
        return prompt


class AutoGenLLMConfig:
    """
    Configuration utilities for AutoGen with local LLM.
    """
    
    @staticmethod
    def patch_autogen():
        """
        Patch AutoGen to use our custom LLM client.
        
        This function should be called before creating any agents.
        """
        if not AUTOGEN_AVAILABLE:
            logger.error("AutoGen is not available, cannot patch.")
            return
            
        logger.info("Patching AutoGen to use local LLM integration...")
        
        try:
            # In AutoGen 0.7.5+, we should use register_model_client
            from autogen.oai import OpenAIWrapper
            
            # Create a wrapper function to create a local LLM client
            def create_local_llm_client(model_name, **config):
                logger.info(f"Creating local LLM client for model: {model_name}")
                return LocalLLMAPIClient(
                    model_path=config.get("model_path"),
                    model_config=config.get("model_config", {})
                )
            
            # Register our custom client factory for local LLM models
            OpenAIWrapper.register_model_client("TinyLlama-1.1B-Chat", create_local_llm_client)
            
            logger.info("Local LLM registered as model client for AutoGen")
            
        except Exception as e:
            logger.error(f"Error patching AutoGen: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            logger.warning("Could not patch AutoGen, will use default behavior")
    
    @staticmethod
    def create_llm_config(agent_name: str, temperature: float = 0.7, 
                        use_local_llm: bool = True) -> Dict[str, Any]:
        """
        Create a configuration for an AutoGen agent.
        
        Args:
            agent_name: Name of the agent
            temperature: Temperature for generation
            use_local_llm: Whether to use the local LLM
            
        Returns:
            LLM configuration dictionary for the agent
        """
        if use_local_llm:
            # Use the registered TinyLlama model directly
            config = {
                "config_list": [
                    {
                        "model": "TinyLlama-1.1B-Chat",
                        "temperature": temperature,
                        "max_tokens": 1024
                    }
                ]
            }
        else:
            # Use OpenAI if available, otherwise fall back to local
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                config = {
                    "config_list": [
                        {
                            "model": "gpt-3.5-turbo",
                            "api_key": api_key,
                            "temperature": temperature
                        }
                    ]
                }
            else:
                logger.warning(f"No OpenAI API key found, falling back to local LLM for {agent_name}")
                config = {
                    "config_list": [
                        {
                            "model": "TinyLlama-1.1B-Chat",
                            "temperature": temperature,
                            "max_tokens": 1024
                        }
                    ]
                }
                
        return config


def clear_model():
    """
    Clear the global model instance to free memory.
    """
    global _MODEL_INSTANCE
    _MODEL_INSTANCE = None
    import gc
    gc.collect()