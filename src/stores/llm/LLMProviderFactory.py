from .LLMEnums import LLMEnums
from .providers import OpenAIProvider, CoHereProvider
from helpers.config import Settings

class LLMProviderFactory:
    def __init__(self, config: Settings):
        self.config = config
        
    def create(self, provider: str):
        if provider == LLMEnums.OPENAI.value:
            return OpenAIProvider(api_key=self.config.OPENAI_API_KEY,
                                  base_url=self.config.OPENAI_BASE_URL,
                                  max_input_characters=self.config.INPUT_DEFAULT_MAX_CHARACTERS,
                                  max_output_tokens=self.config.GENERATION_DAFAULT_MAX_TOKENS,
                                  tempreature=self.config.GENERATION_DAFAULT_TEMPERATURE)
        
        elif provider == LLMEnums.COHERE.value:    
            return CoHereProvider(api_key=self.config.COHER_API_KEY,
                                max_input_characters=self.config.INPUT_DEFAULT_MAX_CHARACTERS,
                                max_output_tokens=self.config.GENERATION_DAFAULT_MAX_TOKENS,
                                tempreature=self.config.GENERATION_DAFAULT_TEMPERATURE)
        
        else:
            return None