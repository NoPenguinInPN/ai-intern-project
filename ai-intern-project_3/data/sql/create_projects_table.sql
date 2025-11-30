DROP TABLE IF EXISTS exchange_projects;
CREATE TABLE exchange_projects (
    id SERIAL PRIMARY KEY,
    project_name TEXT,
    project_type TEXT,
    publish_date DATE,
    source TEXT,
    official_website TEXT,
    exchange_time TEXT,
    quota TEXT,
    cost TEXT,
    major_requirements TEXT,
    language_requirements TEXT,
    gpa_requirements TEXT,
    initial_selection TEXT,
    application_materials TEXT,
    acceptance TEXT,
    deadlines TEXT,
    application_procedure TEXT,
    notes TEXT,
    full_text TEXT
);