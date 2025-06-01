-- Create enum type for material types
CREATE TYPE material_type_enum AS ENUM ('document', 'photo', 'audio', 'video');

-- Create students table with id as BIGINT
CREATE TABLE students (
  id BIGINT PRIMARY KEY,
  name TEXT NOT NULL,
  username TEXT NOT NULL UNIQUE
);

-- Create topics table
CREATE TABLE topics (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  class INTEGER NOT NULL
);

-- Create lessons table with a foreign key to topics
CREATE TABLE lessons (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE
);

-- Create materials table with a foreign key to lessons and using the enum type
CREATE TABLE materials (
  id SERIAL PRIMARY KEY,
  type material_type_enum NOT NULL,
  file_id TEXT NOT NULL,
  lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE
);

-- Create tests table with a foreign key to lessons
CREATE TABLE tests (
  id SERIAL PRIMARY KEY,
  lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
  test_data JSONB NOT NULL,
  CONSTRAINT unique_lesson_test UNIQUE (lesson_id)
);

-- Create quizzes table with a foreign key to topics
CREATE TABLE quizzes (
  id SERIAL PRIMARY KEY,
  topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  test_data JSONB NOT NULL,
  CONSTRAINT unique_topic_quiz UNIQUE (topic_id)
);

-- Create student_scores table with foreign keys to students, tests, and quizzes
CREATE TABLE student_scores (
  id SERIAL PRIMARY KEY,
  student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  test_id INTEGER REFERENCES tests(id) ON DELETE CASCADE,
  quiz_id INTEGER REFERENCES quizzes(id) ON DELETE CASCADE,
  score INTEGER NOT NULL,
  completed_at TIMESTAMP NOT NULL
);