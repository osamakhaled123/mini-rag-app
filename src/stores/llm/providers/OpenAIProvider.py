from ..LLMInterface import LLMInterface
from ..LLMEnums import LLMEnums, OPENAIEnums
from openai import OpenAI
import logging
from typing import List, Union

class OpenAIProvider(LLMInterface):
    def __init__(self, api_key: str, base_url: str, max_input_characters: int=None,
                 max_output_tokens: int=None, tempreature: float=None):
        
        self.api_key = api_key
        self.base_url = base_url
        
        self.max_input_characters=max_input_characters
        self.max_output_tokens = max_output_tokens
        self.tempreature = tempreature
        
        self.generation_model_id = None
        
        self.embedding_model_id = None
        self.embedding_size = None
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url if self.base_url and len(self.base_url) else None,
        )
        
        self.logger = logging.getLogger(__name__)

        self.enums = OPENAIEnums
        
    def process_text(self, text: str):
        return text[:self.max_input_characters].strip()
     
    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id
    
    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size
    
    def generate_texts(self, messages: List, prompt: str, 
                        max_output_token: int=None, tempreature: float=None):
        
        if not self.client:
            self.logger.error(f"{LLMEnums.OPENAI.value} client was not set")
            return None
        
        if not self.generation_model_id:
            self.logger.error(f"{LLMEnums.OPENAI.value} generation model id was not set")
            return None
        
        if not prompt or len(prompt)==0:
            self.logger.error("prompt was not set")
            return None
        
        max_output_token = max_output_token if max_output_token else self.max_output_tokens
        tempreature = tempreature if tempreature else self.tempreature
        
        messages.append(
            self.construct_prompt(prompt=prompt, role=self.enums.USER.value)
        )
        
        print(f"Model: {self.generation_model_id}")
        
        response = self.client.chat.completions.create(model=self.generation_model_id,
                                                messages=messages,
                                                max_tokens=max_output_token,
                                                temperature=tempreature)
        
                

        choice = response.choices[0]

        if choice.finish_reason == "length":
            self.logger.error(
                f"{LLMEnums.OPENAI.value} LLM generation stopped because max_tokens was reached."
            )

        if not choice.message.content:
            self.logger.error(
                f"LLM returned empty content. "
                f"finish_reason={choice.finish_reason}"
            )
            return None

        return choice.message.content
    
    
    def embed_texts(self, texts: Union[str, List[str]], documente_type: str=None):
        if not self.client:
            self.logger.error(f"{LLMEnums.OPENAI.value} client was not set")
            return None
        
        if not self.embedding_model_id:
            self.logger.error(f"{LLMEnums.OPENAI.value} embedding model id was not set")
            return None


        if isinstance(texts, str):
            texts = [texts]
            
        if not texts or len(texts)==0:
            self.logger.error("text to be embedded was not set")
            return None

        response = self.client.embeddings.create(
            model=self.embedding_model_id,
            input=texts,
            encoding_format="float"
        )
        
        if not response or not response.data or not response.data[0].embedding:
            self.logger.error(f"Error while embedding text with {LLMEnums.OPENAI.value}")
            return None
        
        return [response.embedding for response in response.data]
        
    def construct_prompt(self, prompt: str, role: str):
        return {
            self.enums.ROLE.value: role,
            self.enums.CONTENT.value: prompt
        }