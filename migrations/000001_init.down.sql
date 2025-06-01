-- Drop tables in reverse order to handle dependencies
DROP TABLE IF EXISTS student_scores;
DROP TABLE IF EXISTS quizzes;
DROP TABLE IF EXISTS tests;
DROP TABLE IF EXISTS materials;
DROP TABLE IF EXISTS lessons;
DROP TABLE IF EXISTS topics;
DROP TABLE IF EXISTS students;

-- Drop the enum type
DROP TYPE IF EXISTS material_type_enum;