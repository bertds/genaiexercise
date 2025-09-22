"""
Amazon Bedrock Model Constants with Metadata
Contains all model IDs and metadata used across the workshop notebooks
"""

MODELS = {
    "us.amazon.nova-lite-v1:0": {
        "name": "Nova Lite",
        "family": "nova",
        "type": "text",
        "description": "Fast, cost-effective text generation",
        "use_cases": ["summarization", "simple_qa", "basic_text", "entity_extraction"],
        "max_tokens": 300000
    },
    "us.amazon.nova-pro-v1:0": {
        "name": "Nova Pro", 
        "family": "nova",
        "type": "text",
        "description": "Advanced reasoning and complex tasks",
        "use_cases": ["code_generation", "complex_reasoning", "agents", "analysis"],
        "max_tokens": 300000
    },
    "us.amazon.nova-micro-v1:0": {
        "name": "Nova Micro",
        "family": "nova", 
        "type": "text",
        "description": "Ultra-fast responses for simple tasks",
        "use_cases": ["quick_responses", "simple_classification", "basic_chat"],
        "max_tokens": 128000
    },
    "amazon.titan-embed-text-v1": {
        "name": "Titan Text Embeddings v1",
        "family": "titan",
        "type": "embeddings", 
        "description": "Text embeddings for RAG and search",
        "use_cases": ["embeddings", "rag", "similarity_search"],
        "dimensions": 1536
    },
    "amazon.titan-embed-text-v2:0": {
        "name": "Titan Text Embeddings v2",
        "family": "titan",
        "type": "embeddings", 
        "description": "Enhanced text embeddings with better performance",
        "use_cases": ["embeddings", "rag", "similarity_search"],
        "dimensions": 1024
    },
    "amazon.nova-canvas-v1:0": {
        "name": "Nova Canvas",
        "family": "nova",
        "type": "image",
        "description": "Image generation and editing",
        "use_cases": ["image_generation", "image_editing", "visual_content"]
    },
    "amazon.nova-reel-v1:1": {
        "name": "Nova Reel",
        "family": "nova",
        "type": "video",
        "description": "Video generation and editing",
        "use_cases": ["video_generation", "video_editing", "multimedia_content"]
    }
}

# Filtered lists for different use cases
TEXT_MODELS = {k: v for k, v in MODELS.items() if v["type"] == "text"}
EMBEDDING_MODELS = {k: v for k, v in MODELS.items() if v["type"] == "embeddings"}
IMAGE_MODELS = {k: v for k, v in MODELS.items() if v["type"] == "image"}
VIDEO_MODELS = {k: v for k, v in MODELS.items() if v["type"] == "video"}

# Default models for different scenarios
DEFAULT_TEXT_MODEL = "us.amazon.nova-lite-v1:0"
DEFAULT_REASONING_MODEL = "us.amazon.nova-pro-v1:0"
DEFAULT_EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"
DEFAULT_IMAGE_MODEL = "us.amazon.nova-canvas-v1:0"
DEFAULT_VIDEO_MODEL = "amazon.nova-reel-v1:1"
