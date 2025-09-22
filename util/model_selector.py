"""
Interactive Model Selection Widget for Jupyter Notebooks
Provides unified model selection and Bedrock API interface
"""
import boto3
import ipywidgets as widgets
from IPython.display import display
from .model_constants import (EMBEDDING_MODELS, IMAGE_MODELS, MODELS,
                             TEXT_MODELS, VIDEO_MODELS)


class ModelSelector:
    def __init__(self, model_type="text", default_model=None, show_description=True):
        self.model_type = model_type
        self.selected_model = None
        self.show_description = show_description
        
        # Get appropriate models based on type
        if model_type == "text":
            available_models = TEXT_MODELS
        elif model_type == "embeddings":
            available_models = EMBEDDING_MODELS
        elif model_type == "image":
            available_models = IMAGE_MODELS
        elif model_type == "video":
            available_models = VIDEO_MODELS
        else:
            available_models = MODELS
            
        # Create dropdown options
        options = [(f"{v['name']} - {v['description']}", k) 
                  for k, v in available_models.items()]
        
        # Set default model
        if default_model and default_model in available_models:
            default_value = default_model
        else:
            default_value = list(available_models.keys())[0]
        
        # Create widget
        self.dropdown = widgets.Dropdown(
            options=options,
            value=default_value,
            description='Model:',
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='600px')
        )
        
        # Set initial selection
        self.selected_model = self.dropdown.value
        
        # Observe changes
        self.dropdown.observe(self._on_change, names='value')
        
        # Create info display
        self.info_output = widgets.Output()
        self._update_info()
    
    def _on_change(self, change):
        self.selected_model = change['new']
        self._update_info()
    
    def _update_info(self):
        if not self.show_description:
            return
            
        model_info = MODELS[self.selected_model]
        with self.info_output:
            self.info_output.clear_output()
            print(f"✓ Selected: {model_info['name']}")
            print(f"  Family: {model_info['family'].title()}")
            print(f"  Type: {model_info['type'].title()}")
            print(f"  Use Cases: {', '.join(model_info['use_cases'])}")
            if 'max_tokens' in model_info:
                print(f"  Max Tokens: {model_info['max_tokens']:,}")
            if 'dimensions' in model_info:
                print(f"  Dimensions: {model_info['dimensions']}")
    
    def display(self):
        if self.show_description:
            display(widgets.VBox([self.dropdown, self.info_output]))
        else:
            display(self.dropdown)
        return self
    
    def get_model_id(self):
        return self.selected_model
    
    def get_model_info(self):
        return MODELS[self.selected_model]

class BedrockConverse:
    """
    Unified Bedrock API wrapper using Converse API
    Works with all text models (Nova, Claude, Titan, etc.)
    """
    def __init__(self, region_name=None):
        self.client = boto3.client('bedrock-runtime', region_name=region_name)
    
    def converse(self, model_id, messages, max_tokens=1000, temperature=0.3, top_p=0.9, top_k=None):
        """
        Unified converse method using Converse API
        
        Args:
            model_id (str): The model ID to use
            messages (list): List of message objects in converse format
            max_tokens (int): Maximum tokens to generate
            temperature (float): Temperature for randomness (0.0-1.0)
            top_p (float): Top-p sampling parameter (0.0-1.0)
            top_k (int): Top-k sampling parameter (optional)
        
        Returns:
            str: Generated text response
        """
        try:
            # Build inference config
            inference_config = {
                'maxTokens': max_tokens,
                'temperature': temperature,
                'topP': top_p
            }
            
            # Add top_k if specified (not all models support it)
            if top_k is not None:
                inference_config['topK'] = top_k
            
            response = self.client.converse(
                modelId=model_id,
                messages=messages,
                inferenceConfig=inference_config
            )
            
            return response['output']['message']['content'][0]['text']
            
        except Exception as e:
            print(f"Error invoking model {model_id}: {str(e)}")
            return None

# Convenience functions for different model types
def create_text_model_selector(default=None, show_description=True):
    """Create a text model selector widget"""
    return ModelSelector("text", default or "us.amazon.nova-lite-v1:0", show_description)

def create_embedding_model_selector(default=None, show_description=True):
    """Create an embedding model selector widget"""
    return ModelSelector("embeddings", default or "amazon.titan-embed-text-v2:0", show_description)

def create_image_model_selector(default=None, show_description=True):
    """Create an image model selector widget"""
    return ModelSelector("image", default or "us.amazon.nova-canvas-v1:0", show_description)

def create_video_model_selector(default=None, show_description=True):
    """Create a video model selector widget"""
    return ModelSelector("video", default or "us.amazon.nova-reel-v1:0", show_description)

# Global instance for easy access
bedrock = BedrockConverse()

# Helper function to create standard message format
def create_message(text, role="user"):
    """
    Create a standard message format for the Converse API
    
    Args:
        text (str): The message text
        role (str): The role ('user' or 'assistant')
    
    Returns:
        dict: Formatted message object
    """
    return {
        "role": role,
        "content": [{"text": text}]
    }

def create_messages(user_text):
    """
    Create a simple messages list with a single user message
    
    Args:
        user_text (str): The user's message text
    
    Returns:
        list: List containing a single user message
    """
    return [create_message(user_text, "user")]
