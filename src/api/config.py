"""
Configuration settings for the API with nested structure
"""
import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional, List, Dict, Any
from pathlib import Path


class ServerSettings(BaseSettings):
    """Server configuration settings"""
    exe_path: Optional[str] = None
    log_path: Optional[str] = None
    cache_dir: Optional[str] = None

    model_config = SettingsConfigDict(
        env_prefix="SERVER_",
        case_sensitive=True,
    )


class CompletionParamsSettings(BaseSettings):
    """Completion parameters for a specific model"""
    # Basic generation parameters
    temperature: float = 0.7
    max_tokens: int = 2000
    # top_p: float = 1.0
    # top_k: int = 40
    # repeat_penalty: float = 1.1
    # frequency_penalty: float = 0.0
    # presence_penalty: float = 0.0

    # # Advanced parameters
    # min_p: float = 0.05
    # tfs_z: float = 1.0
    # typical_p: float = 1.0
    # mirostat: int = 0
    # mirostat_tau: float = 5.0
    # mirostat_eta: float = 0.1

    # # Token handling
    # repeat_last_n: int = 64
    # penalize_newline: bool = True
    # add_bos_token: bool = True
    # ban_eos_token: bool = False
    # skip_special_tokens: bool = True

    # # Streaming and seed
    # stream: bool = False
    # seed: int = -1

    # # Stop sequences
    # stop: Optional[List[str]] = None

    # Custom parameters
    custom_params: Dict[str, Any] = Field(default_factory=dict)

    model_config = SettingsConfigDict(
        case_sensitive=True,
        extra='allow',
    )

    def __init__(self, *args, **kwargs):
        """Initialize CompletionParamsSettings, separating valid fields from custom parameters"""
        # Handle custom parameters
        valid_fields = set(self.model_fields.keys())
        completion_kwargs = {}
        custom_params = {}

        # Extract custom_params if already provided
        if 'custom_params' in kwargs:
            custom_params = kwargs.pop('custom_params', {})
            if not isinstance(custom_params, dict):
                custom_params = {}

        # Separate valid fields from custom parameters
        for key, value in list(kwargs.items()):
            if key in valid_fields:
                completion_kwargs[key] = value
            else:
                custom_params[key] = value

        # Add custom_params back if there are any
        if custom_params:
            completion_kwargs['custom_params'] = custom_params

        # Call parent __init__ with processed kwargs
        super().__init__(*args, **completion_kwargs)


class ServingParamsSettings(BaseSettings):
    """Serving parameters for llamacpp model deployment"""
    seed: Optional[int] = 0
    port: int = 13141
    host: str = "0.0.0.0"
    ctx_size: int = 16384
    main_gpu: int = 0
    parallel: int = 1
    n_gpu_layers: int = 100
    log_verbosity: int = 9
    ssd_kv_offload_gb: int = 100
    dram_kv_offload_gb: int = 0

    # # Reasoning and template settings
    # reasoning_format: Optional[str] = None  # e.g., "deepseek"
    # use_jinja: bool = False

    # # Batch and context settings
    # n_ubatch: int = 512
    # n_batch: int = 512
    # n_parallel: int = 1
    # n_ctx: int = 2048

    # # Generation parameters (for llamacpp serving)
    # temp: float = 0.8
    # top_p: float = 0.95
    # top_k: int = 40
    # min_p: float = 0.05

    # Custom parameters for additional llamacpp serving args
    custom_params: Dict[str, Any] = Field(default_factory=dict)

    model_config = SettingsConfigDict(
        case_sensitive=True,
        extra='allow',
    )

    def __init__(self, *args, **kwargs):
        """Initialize ServingParamsSettings, separating valid fields from custom parameters"""
        # Handle custom parameters
        valid_fields = set(self.model_fields.keys())
        serving_kwargs = {}
        custom_params = {}

        # Extract custom_params if already provided
        if 'custom_params' in kwargs:
            custom_params = kwargs.pop('custom_params', {})
            if not isinstance(custom_params, dict):
                custom_params = {}

        # Separate valid fields from custom parameters
        for key, value in list(kwargs.items()):
            if key in valid_fields:
                serving_kwargs[key] = value
            else:
                custom_params[key] = value

        # Add custom_params back if there are any
        if custom_params:
            serving_kwargs['custom_params'] = custom_params

        # Call parent __init__ with processed kwargs
        super().__init__(*args, **serving_kwargs)


class LocalModelSettings(BaseSettings):
    """Local model configuration for self-hosted models"""
    model_name_or_path: str
    serving_name: Optional[str] = None
    tokenizer: Optional[str] = None  # HuggingFace tokenizer identifier
    model_type: str = "local"

    # Completion parameters for this model
    completion_params: CompletionParamsSettings = Field(default_factory=CompletionParamsSettings)

    # Serving parameters for llamacpp deployment (optional)
    serving_params: Optional[ServingParamsSettings] = None

    model_config = SettingsConfigDict(
        env_prefix="LOCAL_MODEL_",
        case_sensitive=True,
    )

    def model_post_init(self, __context) -> None:
        """Auto-compute serving name if not provided"""
        if self.serving_name is None:
            self.serving_name = self.model_name_or_path


class RemoteModelSettings(BaseSettings):
    """Remote model configuration for external models (cloud APIs, other computers, etc.)"""
    provider: str  # "openai", "azure", "anthropic", "google", "local_remote", etc.
    model: str  # Model identifier (e.g., "gpt-4o-mini", "claude-3-sonnet", "llama-3.1-8b")
    serving_name: Optional[str] = None
    tokenizer: Optional[str] = None  # HuggingFace tokenizer identifier
    base_url: str
    api_key: str
    model_type: str = "remote"

    # Completion parameters for this model
    completion_params: CompletionParamsSettings = Field(default_factory=CompletionParamsSettings)

    model_config = SettingsConfigDict(
        env_prefix="REMOTE_MODEL_",
        case_sensitive=True,
    )

    def model_post_init(self, __context) -> None:
        """Auto-compute serving name if not provided"""
        if self.serving_name is None:
            self.serving_name = self.model


class ModelSettings(BaseSettings):
    """Unified model configuration - supports both local and remote models"""
    model_name_or_path: Optional[str] = None
    serving_name: Optional[str] = None
    tokenizer: Optional[str] = None  # HuggingFace tokenizer identifier
    model_type: str = "local"  # "local" or "remote"

    # For remote models
    provider: Optional[str] = None  # Only for remote models

    # API settings for this model
    base_url: Optional[str] = None  # Default: None
    api_key: Optional[str] = "empty"  # Default: "empty" (must be configured for LLM service)

    # Completion parameters for this model
    completion_params: CompletionParamsSettings = Field(default_factory=CompletionParamsSettings)

    # Serving parameters for llamacpp deployment (only for local models, optional)
    serving_params: Optional[ServingParamsSettings] = None

    model_config = SettingsConfigDict(
        env_prefix="MODEL_",
        case_sensitive=True,
    )

    def model_post_init(self, __context) -> None:
        """Auto-compute serving name if not provided"""
        if self.serving_name is None:
            self.serving_name = self.model_name_or_path

        # Convert None api_key to "empty"
        if self.api_key is None:
            self.api_key = "empty"


class APISettings(BaseSettings):
    """API general settings"""
    title: str = "KVCache Chatbot API"
    version: str = "1.0.0"
    prefix: str = "/api/v1"

    # Session settings
    session_timeout: int = 3600  # 1 hour in seconds

    model_config = SettingsConfigDict(
        env_prefix="API_",
        case_sensitive=True,
    )


class DocumentSettings(BaseSettings):
    """Document management settings"""
    upload_dir: str = "uploads"
    max_file_size: int = 50 * 1024 * 1024  # 50MB (increased for PDF files)
    allowed_extensions: List[str] = [".pdf"]

    # Chunking settings for PDF documents
    chunk_size: int = 10000  # Maximum characters per chunk
    chunk_overlap: int = 200  # Overlap between chunks for context continuity

    # Tokenizer settings
    # If set, will use this model's tokenizer to count tokens in chunks
    # Should match a serving_name or model_name_or_path from models config
    tokenizer_model: Optional[str] = None

    # First-stage grouping settings (token-based sequential merging)
    grouping: bool = True  # Enable token-based grouping when tokenizer available
    file_max_tokens: int = 40000  # Maximum tokens per merged group
    utilization_threshold: float = 0.8  # Minimum utilization for final group (0.0-1.0)

    # Stage-2 similarity grouping settings
    similarity_method: str = "bm25"  # bm25 | embedding
    similarity_min_score: float | None = None  # optional BM25 threshold

    model_config = SettingsConfigDict(
        env_prefix="DOCUMENT_",
        case_sensitive=True,
    )


class PromptsSettings(BaseSettings):
    """Prompt template settings for RAG and document context"""
    system_prompt_template: str = """### Task:
Respond to the user query using the provided context.

### Guidelines:
- If you don't know the answer, clearly state that.
- Respond in the same language as the user's query.

### Output:
Provide a clear and direct response to the user's query.

<context>
{doc_context}
</context>"""

    user_prompt_template: str = """<user_query>
{user_query}
</user_query>"""

    model_config = SettingsConfigDict(
        env_prefix="PROMPTS_",
        case_sensitive=True,
    )


class Settings(BaseSettings):
    """Main application settings with nested configuration"""

    # Nested settings
    api: APISettings = Field(default_factory=APISettings)
    server: ServerSettings = Field(default_factory=ServerSettings)

    # New model configuration structure
    models: Dict[str, List[ModelSettings]] = Field(default_factory=dict)
    # Legacy support - will be populated from new structure
    all_models: List[ModelSettings] = Field(default_factory=list)

    documents: DocumentSettings = Field(default_factory=DocumentSettings)
    prompts: PromptsSettings = Field(default_factory=PromptsSettings)

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent / ".env"),
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore',  # Ignore extra environment variables
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_yaml_config()
        self._validate_config()

    def _load_yaml_config(self):
        """Load configuration from YAML file and merge with current settings"""
        yaml_file = Path(__file__).parent / "env.yaml"
        if not yaml_file.exists():
            print(f"⚠️  YAML config file not found: {yaml_file}")
            return

        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f) or {}

            # Load API settings
            if 'api' in yaml_data:
                api_data = yaml_data['api']
                self.api = APISettings(
                    title=api_data.get('title', self.api.title),
                    version=api_data.get('version', self.api.version),
                    prefix=api_data.get('prefix', self.api.prefix),
                    session_timeout=api_data.get('session_timeout', self.api.session_timeout)
                )

            # Load server settings
            if 'server' in yaml_data:
                server_data = yaml_data['server']
                self.server = ServerSettings(
                    exe_path=server_data.get('exe_path'),
                    log_path=server_data.get('log_path'),
                    cache_dir=server_data.get('cache_dir')
                )

            # Load models settings - new structure
            if 'models' in yaml_data:
                models_data = yaml_data['models']
                self.models = {}
                self.all_models = []

                # Process local models
                if 'local_models' in models_data:
                    self.models['local_models'] = []
                    for model_data in models_data['local_models']:
                        model_settings = self._create_model_settings(model_data, "local")
                        self.models['local_models'].append(model_settings)
                        self.all_models.append(model_settings)

                # Process remote models (cloud APIs, other computers, etc.)
                if 'remote_models' in models_data:
                    self.models['remote_models'] = []
                    for model_data in models_data['remote_models']:
                        model_settings = self._create_model_settings(model_data, "remote")
                        self.models['remote_models'].append(model_settings)
                        self.all_models.append(model_settings)

                # Legacy support: if models is a list (old format)
                elif isinstance(models_data, list):
                    self.models['legacy'] = []
                    for model_data in models_data:
                        model_settings = self._create_model_settings(model_data, "local")
                        self.models['legacy'].append(model_settings)
                        self.all_models.append(model_settings)

            # Load documents settings
            if 'documents' in yaml_data:
                documents_data = yaml_data['documents']
                self.documents = DocumentSettings(
                    upload_dir=documents_data.get('upload_dir', self.documents.upload_dir),
                    max_file_size=documents_data.get('max_file_size', self.documents.max_file_size),
                    allowed_extensions=documents_data.get('allowed_extensions', self.documents.allowed_extensions),
                    chunk_size=documents_data.get('chunk_size', self.documents.chunk_size),
                    chunk_overlap=documents_data.get('chunk_overlap', self.documents.chunk_overlap),
                    tokenizer_model=documents_data.get('tokenizer_model', self.documents.tokenizer_model),
                    grouping=documents_data.get('grouping', self.documents.grouping),
                    file_max_tokens=documents_data.get('file_max_tokens', self.documents.file_max_tokens),
                    utilization_threshold=documents_data.get('utilization_threshold', self.documents.utilization_threshold),
                    similarity_method=documents_data.get('similarity_method', self.documents.similarity_method),
                    similarity_min_score=documents_data.get('similarity_min_score', self.documents.similarity_min_score)
                )

            # Load prompts settings
            if 'prompts' in yaml_data:
                prompts_data = yaml_data['prompts']
                self.prompts = PromptsSettings(
                    system_prompt_template=prompts_data.get('system_prompt_template', self.prompts.system_prompt_template),
                    user_prompt_template=prompts_data.get('user_prompt_template', self.prompts.user_prompt_template)
                )

            print("✅ YAML configuration loaded successfully")

        except Exception as e:
            print(f"❌ Error loading YAML config: {e}")

    def _create_model_settings(self, model_data: dict, model_type: str) -> ModelSettings:
        """Create ModelSettings from YAML data"""
        # Load completion params for this model
        # CompletionParamsSettings.__init__ will automatically handle custom_params separation
        completion_params_data = model_data.get('completion_params', {})
        completion_params = CompletionParamsSettings(**completion_params_data)

        # Load serving params for local models (optional)
        serving_params = None
        if model_type == "local":
            serving_params_data = model_data.get('serving_params')
            if serving_params_data:
                # ServingParamsSettings.__init__ will automatically handle custom_params separation
                serving_params = ServingParamsSettings(**serving_params_data)

        # Create model settings based on type
        if model_type == "local":
            return ModelSettings(
                model_name_or_path=model_data.get('model_name_or_path'),
                serving_name=model_data.get('serving_name'),
                tokenizer=model_data.get('tokenizer'),
                model_type="local",
                base_url=model_data.get('base_url'),  # Support base_url for local models
                api_key=model_data.get('api_key', "not-needed"),  # Support api_key for local models
                completion_params=completion_params,
                serving_params=serving_params
            )
        else:  # remote
            return ModelSettings(
                model_name_or_path=model_data.get('model'),  # For remote, use 'model' as model_name_or_path
                serving_name=model_data.get('serving_name'),
                tokenizer=model_data.get('tokenizer'),
                model_type="remote",
                provider=model_data.get('provider'),
                base_url=model_data.get('base_url'),
                api_key=model_data.get('api_key'),
                completion_params=completion_params
            )

    def _validate_config(self):
        """Validate the complete configuration"""
        # Validate at least one model is configured
        if not self.models and not self.all_models:
            print("⚠️  No models configured")
        else:
            # Validate local models
            if 'local_models' in self.models:
                print(f"✅ Local models configured: {len(self.models['local_models'])}")
                for i, model in enumerate(self.models['local_models']):
                    if not model.model_name_or_path:
                        print(f"⚠️  Local model {i+1} missing model_name_or_path")
                    else:
                        print(f"  ✅ {model.serving_name or model.model_name_or_path}")

            # Validate remote models
            if 'remote_models' in self.models:
                print(f"✅ Remote models configured: {len(self.models['remote_models'])}")
                for i, model in enumerate(self.models['remote_models']):
                    if not model.model_name_or_path:
                        print(f"⚠️  Remote model {i+1} missing model identifier")
                    else:
                        provider_info = f" ({model.provider})" if model.provider else ""
                        print(f"  ✅ {model.serving_name or model.model_name_or_path}{provider_info}")

        # Validate server settings
        if self.server.exe_path:
            print(f"✅ Server configured: {self.server.exe_path}")
        else:
            print("⚠️  Server exe_path not configured")

    def get_tokenizer_for_model(self, model_identifier: Optional[str] = None) -> Optional[str]:
        """
        Get the tokenizer string for a given model identifier

        Args:
            model_identifier: serving_name or model_name_or_path,
                            or None to automatically use the first model with tokenizer

        Returns:
            Tokenizer string (HuggingFace identifier) or None if not configured
        """
        # If specific model identifier provided, search for that model
        if model_identifier:
            for model in self.all_models:
                if model.serving_name == model_identifier or model.model_name_or_path == model_identifier:
                    return model.tokenizer
            return None

        # If tokenizer_model is set in documents config, use that
        if self.documents.tokenizer_model:
            for model in self.all_models:
                if model.serving_name == self.documents.tokenizer_model or model.model_name_or_path == self.documents.tokenizer_model:
                    return model.tokenizer

        # Otherwise, automatically use the first model that has a tokenizer configured
        for model in self.all_models:
            if model.tokenizer:
                return model.tokenizer

        return None

    def get_local_models(self) -> List[ModelSettings]:
        """Get all local models"""
        return self.models.get('local_models', [])

    def get_remote_models(self) -> List[ModelSettings]:
        """Get all remote models"""
        return self.models.get('remote_models', [])

    def get_model_by_serving_name(self, serving_name: str) -> Optional[ModelSettings]:
        """Get model by serving name from all models"""
        for model in self.all_models:
            if model.serving_name == serving_name:
                return model
        return None

    def get_models_by_type(self, model_type: str) -> List[ModelSettings]:
        """Get models by type (local or remote)"""
        if model_type == "local":
            return self.get_local_models()
        elif model_type == "remote":
            return self.get_remote_models()
        else:
            return []


# Create global settings instance
settings = Settings()
