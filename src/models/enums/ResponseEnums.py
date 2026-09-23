from enum import Enum

class ResponseSignal(Enum):
    FILE_VALIDATED_SUCCESS = "file_validate_successfully"
    FILE_TYPE_NOT_SUPPORTED = "file_type_not_supported"
    FILE_SIZE_EXCEEDED = "file_size_exceeded"
    FILE_UPLOAD_SUCCESS = "file_upload_success"
    FILE_UPLOAD_FAILED = "file_upload_failed"
    FILE_PROCESSING_SUCCESS = "file_processed_successfully"
    FILE_PROCESSING_FAILED = "file_processing_failed"
    NO_FILES_ERROR = "not_found_files"
    FILE_ID_ERROR = "no_file_found_with_this_id"
    PROJECT_NOT_FOUND_ERROR = "project_not_found"
    INSERT_INTO_VECTORDB_ERROR = "insert_into_vectordb_error"
    INSERT_INTO_VECTORDB_SUCCESSS =  "insert_into_vectordb_success"
    VECTORDB_COLLECTION_RETRIEVED = "vectordb_collection_retrieved"
    VECTORDB_COLLECTION_INFO_ERROR = "vectordb_collection_info_error"
    VECTORDB_SEARCH_ERROR = "vectordb_search_error"
    VECTORDB_SEARCH_SUCCESS = "vectordb_search_success"
    RAG_ANSWER_ERROR = "RAG_answer_error"
    RAG_ANSWER_SUCCESS = "RAG_answer_success"
    DOCUMENT_DELETED_FROM_DISK = "document_deleted_from_disk"
    DOCUMENT_ASSET_DELETED_FROM_DATABASE = "document_asset_deleted_from_database"
    DOCUMENT_ASSET_DELETED_FROM_DATABASE_ERROR = "document_asset_Not_found_in_database"
    DOCUMENT_CHUNKS_DELETED_FROM_DATABASE = "chunks_deleted_from_database"
    DOCUMENT_CHUNKS_DELETED_FROM_DATABASE_ERROR = "chunks_deleted_from_database_error"
    DOCUMENT_CHUNKS_DELETED_FROM_VECTORDB = "chunks_deleted_from_vectordb"
    DOCUMENT_CHUNKS_DELETED_FROM_VECTORDB_ERROR = "chunks_deleted_from_vectordb_error"
    FILE_PASSED_TO_DELETE_NOT_REMOVED = "file_passed_to_delete_not_removed"
    
    
    