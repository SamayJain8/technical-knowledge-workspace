CREATE TABLE documents (
    document_id VARCHAR2(64) PRIMARY KEY,
    title VARCHAR2(512) NOT NULL,
    source_url VARCHAR2(2048),
    provenance VARCHAR2(2000) NOT NULL,
    ingested_at TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);
CREATE TABLE document_chunks (
    chunk_id VARCHAR2(64) PRIMARY KEY,
    document_id VARCHAR2(64) NOT NULL REFERENCES documents(document_id),
    chunk_number NUMBER(10) NOT NULL CHECK (chunk_number >= 0),
    chunk_text CLOB NOT NULL,
    embedding VECTOR(384, FLOAT32) NOT NULL,
    embedding_version VARCHAR2(64) NOT NULL,
    CONSTRAINT chunk_position_unique UNIQUE (document_id, chunk_number)
);
