from enum import Enum

class LLMEnums(Enum):
    OPENAI="OpenAI"
    COHERE="Cohere"
    
    
class DocumentTypeEnums(Enum):
    DOCUMENT="document"
    QUERY="query"

class OPENAIEnums(Enum):
    SYSTEM="system"
    USER="user"
    ASSISTANT="assistant"
    DEVELOPER="developer"

    ROLE="role"
    CONTENT="content"
    
class COHEREEnums(Enum):
    SYSTEM="system"
    USER="user"
    ASSISTANT="assistant"    
    
    ROLE="role"
    CONTENT="content"
    
    DOCUMENT="search_document"
    QUERY="search_query"