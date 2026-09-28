from enum import Enum

class VectorDBEnums(Enum):
    QDRANT = "QDrant"
    PGVECTOR = "PGVector"
    
class DistanceMethodEnums(Enum):
    COSINE="cosine"
    DOT="dot"
    
class PGVectorTableSchemeEnums(Enum):
    ID = "id"
    TEXT = "text"
    VECTOR = "vector"
    CHUNK_ID = "chunk_id"
    METADATA = "metadata"

class PGVectorDistanceMethodEnums(Enum):
    COSINE="vector_cosine_ops"
    DOT="vector_ip_ops"
    EUCLIDEAN="vector_l2_ops"
    MANHATTAN="vector_l1_ops"

class PGVectorSimilaritySearchMethodEnums(Enum):
    COSINE="<=>"
    DOT="<#>"
    EUCLIDEAN="<->"
    MANHATTAN="<+>"    

class IndexingTypeEnums(Enum):
    HNSW="hnsw"
    IVFFLAT="ivfflat"
            