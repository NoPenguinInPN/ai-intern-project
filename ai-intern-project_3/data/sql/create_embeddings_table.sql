DROP TABLE IF EXISTS embeddings;

CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    index INT,
    embedding VECTOR(1024)
);