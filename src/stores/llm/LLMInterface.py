from abc import ABC, abstractmethod
from typing import List

class LLMInterface(ABC):
    
    @abstractmethod
    def set_generation_model(self, model_id: str):
        pass
    
    @abstractmethod
    def set_embedding_model(self, model_id: str, embedding_size: int):
        pass
    
    @abstractmethod
    def generate_texts(self, messages: List, prompt: str, 
                      max_output_token: int=None, tempreature: float=None):
        pass
        
    @abstractmethod
    def embed_texts(self, text: str, documente_type: str=None):
        pass   
        
    @abstractmethod
    def construct_prompt(self, prompt: str, role: str):
        pass