import json
from typing import Dict, List, Optional

from bot.services.database.models import QuizData, QuizQuestion, Topic


class QuizRepository:
    def __init__(self, db):
        self.db = db

    async def get_quiz(self, topic_id: int) -> Optional[QuizData]:
        """Get full quiz data for a topic."""
        query = """
            SELECT test_data::text
            FROM quizzes 
            WHERE topic_id = $1
        """
        result = await self.db.fetchval(query, topic_id)
        if result:
            data = json.loads(result)
            return QuizData.model_validate(data)
        return None

    async def add_quiz(self, topic_id: int, quiz_data: QuizData) -> int:
        """Add or update quiz for a topic. Returns quiz ID."""
        query = """
            INSERT INTO quizzes (topic_id, test_data)
            VALUES ($1, $2::jsonb)
            ON CONFLICT ON CONSTRAINT unique_topic_quiz
            DO UPDATE SET test_data = $2::jsonb
            RETURNING id
        """
        json_data = quiz_data.model_dump_json()
        return await self.db.fetchval(query, topic_id, json_data)

    async def get_question(
        self, topic_id: int, question_index: int
    ) -> Optional[QuizQuestion]:
        """Get a specific question from a topic's quiz."""
        query = """
            SELECT (test_data->'questions'->$2::int)
            FROM quizzes 
            WHERE topic_id = $1
        """
        result = await self.db.fetchval(query, topic_id, question_index)
        if result:
            data = json.loads(result)
            return QuizQuestion.model_validate(data)
        return None

    async def save_student_score(
        self, student_id: int, topic_id: int, score: int
    ) -> int:
        """Save student's quiz score."""
        # First get quiz_id for the topic
        quiz_id = await self.db.fetchval(
            "SELECT id FROM quizzes WHERE topic_id = $1", topic_id
        )
        if not quiz_id:
            raise ValueError("No quiz found for this topic")

        query = """
            INSERT INTO student_scores (
                student_id, 
                quiz_id, 
                score, 
                completed_at
            )
            VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
            RETURNING id
        """
        return await self.db.fetchval(query, student_id, quiz_id, score)

    async def get_eligible_topics(
        self, student_id: int, min_lesson_score: int
    ) -> List[Topic]:
        """Returns a list of topics where the student can take the quiz."""
        query = """
            SELECT t.id, t.title, t.description, t.class
            FROM topics t
            JOIN quizzes q ON t.id = q.topic_id
            WHERE NOT EXISTS (
                -- Check if the student failed any test in this topic
                SELECT 1 FROM lessons l
                JOIN tests tst ON l.id = tst.lesson_id
                LEFT JOIN student_scores s ON tst.id = s.test_id AND s.student_id = $1
                WHERE l.topic_id = t.id
                GROUP BY l.id, tst.id
                HAVING COALESCE(MAX(s.score), 0) < $2
            )
            AND NOT EXISTS (
                -- Check if the student has already taken the quiz
                SELECT 1 FROM student_scores sq
                WHERE sq.quiz_id = q.id AND sq.student_id = $1
            );
        """
        results = await self.db.fetch(query, student_id, min_lesson_score)

        return [Topic(**row) for row in results]

    async def get_student_highest_score(
        self, student_id: int, topic_id: int
    ) -> Optional[Dict]:
        """
        Get student's highest score for a topic's quiz.
        Returns dict with score and completion date, or None if no attempts.
        """
        query = """
            SELECT 
                s.score,
                s.completed_at
            FROM student_scores s
            JOIN quizzes q ON s.quiz_id = q.id
            WHERE s.student_id = $1 
            AND q.topic_id = $2
            ORDER BY s.score DESC
            LIMIT 1
        """
        result = await self.db.fetchrow(query, student_id, topic_id)
        return dict(result) if result else None
