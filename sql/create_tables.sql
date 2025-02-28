-- Create PARAMETERS table
CREATE TABLE parameters (
  param_id SERIAL PRIMARY KEY,
  test_name VARCHAR(100),
  description VARCHAR(255),
  creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create TEMPLATE table
CREATE TABLE template (
  template_id SERIAL PRIMARY KEY,
  template_name VARCHAR(100),
  template_text TEXT
);

-- Create MESSAGES table
CREATE TABLE messages (
  message_id SERIAL PRIMARY KEY,
  template_id INT NOT NULL REFERENCES template(template_id),
  param_id INT REFERENCES parameters(param_id),
  generated_text TEXT,
  creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create EXPECTED_RESULTS table
CREATE TABLE expected_results (
  message_id INT PRIMARY KEY REFERENCES messages(message_id),
  expected_label VARCHAR(100)
);

-- Create ACTUAL_RESULTS table
CREATE TABLE actual_results (
  message_id INT REFERENCES messages(message_id),
  model_version VARCHAR(50),
  predicted_label VARCHAR(100),
  confidence REAL,
  classification_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);