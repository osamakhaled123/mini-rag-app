from ..LLMInterface import LLMInterface
from ..LLMEnums import LLMEnums, COHEREEnums, DocumentTypeEnums
import cohere
import logging
from typing import List, Union

class CoHereProvider(LLMInterface):
    def __init__(self, api_key: str, max_input_characters: int=None,
                 max_output_tokens: int=None, tempreature: float=None):
        
        self.api_key = api_key
        
        self.max_input_characters=max_input_characters
        self.max_output_tokens = max_output_tokens
        self.tempreature = tempreature
        
        self.generation_model_id = None
        
        self.embedding_model_id = None
        self.embedding_size = None
        
        self.client = cohere.ClientV2(
            api_key=self.api_key
        )
        
        self.logger = logging.getLogger(__name__)

        self.enums = COHEREEnums
        
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
            self.logger.error(f"{LLMEnums.COHERE.value} client was not set")
            return None
        
        if not self.generation_model_id:
            self.logger.error(f"{LLMEnums.COHERE.value} generation model id was not set")
            return None
        
        if not prompt or len(prompt)==0:
            self.logger.error("prompt was not set")
            return None
        
        max_output_token = max_output_token if max_output_token else self.max_output_tokens
        tempreature = tempreature if tempreature else self.tempreature
        
        messages.append(
            self.construct_prompt(prompt=prompt, role=self.enums.USER.value)
        )
        
        response = self.client.chat(model=self.generation_model_id,
                                                messages=messages,
                                                max_tokens=max_output_token,
                                                temperature=tempreature)
        
        if not response or not response.message or len(response.message.content)==0 or not response.message.content[0] or not response.message.content[0].text:
            self.logger.error(f"Error while generating text with {LLMEnums.COHERE.value}")
            return None
        
        return response.message.content[0].text
    
    
    def embed_texts(self, texts: Union[str, List[str]], documente_type: str=None):
        if not self.client:
            self.logger.error(f"{LLMEnums.COHERE.value} client was not set")
            return None
        
        if not self.embedding_model_id:
            self.logger.error(f"{LLMEnums.COHERE.value} embedding model id was not set")
            return None

        input_type = self.enums.DOCUMENT.value
        if documente_type == DocumentTypeEnums.QUERY.value:
            input_type = self.enums.QUERY.value
            
        if isinstance(texts, str):
            texts = [texts]
            
        processed_texts = [self.process_text(t) for t in texts]
        
        response = self.client.embed(
            model=self.embedding_model_id,
            input_type=input_type,
            texts=processed_texts,
            embedding_types=["float"],
            output_dimension=self.embedding_size
        )
        
        if not response or not response.embeddings or not response.embeddings.float or len(response.embeddings.float)==0:
            self.logger.error(f"Error while embedding text with {LLMEnums.COHERE.value}")
            return None
        
        return response.embeddings.float
        
    def construct_prompt(self, prompt: str, role: str):
        return {
            self.enums.ROLE.value: role,
            self.enums.CONTENT.value: prompt
        }