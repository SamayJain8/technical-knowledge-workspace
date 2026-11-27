DECLARE
    found NUMBER;
BEGIN
    SELECT COUNT(*) INTO found FROM user_tab_columns
      WHERE table_name = 'DOCUMENTS' AND column_name = 'DOCUMENT_TYPE';
    IF found = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE documents ADD (
            document_type VARCHAR2(8) DEFAULT ''seed'' NOT NULL,
            content_hash VARCHAR2(64) UNIQUE,
            page_count NUMBER(6),
            byte_count NUMBER(12),
            external_ok NUMBER(1) DEFAULT 0 NOT NULL CHECK (external_ok IN (0, 1)),
            CHECK (document_type IN (''seed'', ''pdf'', ''txt'', ''md''))
        )';
    END IF;
    SELECT COUNT(*) INTO found FROM user_tab_columns
      WHERE table_name = 'DOCUMENT_CHUNKS' AND column_name = 'PAGE_NUMBER';
    IF found = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE document_chunks ADD (page_number NUMBER(6))';
    END IF;
END;
/
