from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Student(BaseModel):
    id: int
    name: str
    username: str


class Topic(BaseModel):
    id: int
    title: str
    description: str
    class_number: int = Field(alias="class")


class Lesson(BaseModel):
    id: int
    title: str
    description: str
    topic_id: int


class Material(BaseModel):
    id: int
    lesson_id: int
    file_id: str
    type: str


class QuizScore(BaseModel):
    id: int
    student_id: int
    quiz_id: int
    score: int
    completed_at: datetime


class QuizQuestion(BaseModel):
    """Model representing a single quiz question"""

    question: str
    options: List[str]
    correct_answer: int = Field(ge=0)  # Index of correct answer, zero-based


class QuizData(BaseModel):
    """Model representing full quiz data"""

    questions: List[QuizQuestion]


class Quiz(BaseModel):
    """Model representing a quiz entry in database"""

    id: int
    topic_id: int
    test_data: QuizData

    @property
    def question_count(self) -> int:
        return len(self.test_data.questions)

    def get_question(self, index: int) -> Optional[QuizQuestion]:
        """Get question by index"""
        if 0 <= index < self.question_count:
            return self.test_data.questions[index]
        return None


class TestQuestion(BaseModel):
    """Model representing a single test question"""

    question: str
    options: List[str]
    correct_answer: int = Field(ge=0)  # Index of correct answer, zero-based


class TestData(BaseModel):
    """Model representing full test data"""

    questions: List[TestQuestion]


class Test(BaseModel):
    """Model representing a test entry in database"""

    id: int
    lesson_id: int
    test_data: TestData

    @property
    def question_count(self) -> int:
        return len(self.test_data.questions)

    def get_question(self, index: int) -> Optional[TestQuestion]:
        """Get question by index"""
        if 0 <= index < self.question_count:
            return self.test_data.questions[index]
        return None


class TestScore(BaseModel):
    id: int
    student_id: int
    test_id: int
    score: int
    completed_at: datetime
