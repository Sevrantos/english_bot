import json
from typing import Dict, Optional

from bot.services.database.models import TestData, TestQuestion


class TestRepository:
    def __init__(self, db):
        self.db = db

    async def get_question(
        self, lesson_id: int, question_index: int
    ) -> Optional[TestQuestion]:
        """Get a specific question from a lesson's test.

        Args:
            lesson_id: The ID of the lesson
            question_index: Zero-based index of the question to retrieve

        Returns:
            TestQuestion object if found, None otherwise
        """
        query = """
            SELECT (test_data->'questions'->$2::int)
            FROM tests 
            WHERE lesson_id = $1
        """
        result = await self.db.fetchval(query, lesson_id, question_index)
        if result:
            if isinstance(result, str):
                result = json.loads(result)
            return TestQuestion.model_validate(result)
        return None

    async def get_test(self, lesson_id: int) -> Optional[TestData]:
        """Get full test data for a lesson."""
        query = """
            SELECT test_data::text
            FROM tests 
            WHERE lesson_id = $1
        """
        result = await self.db.fetchval(query, lesson_id)
        if result:
            data = json.loads(result)
            return TestData.model_validate(data)
        return None

    async def add_test(self, lesson_id: int, test_data: TestData) -> int:
        """Add or update test for a lesson. Returns test ID."""
        query = """
            INSERT INTO tests (lesson_id, test_data)
            VALUES ($1, $2::jsonb)
            ON CONFLICT (lesson_id) DO UPDATE
            SET test_data = $2::jsonb
            RETURNING id
        """
        json_data = test_data.model_dump_json()
        return await self.db.fetchval(query, lesson_id, json_data)

    async def save_student_score(
        self, student_id: int, lesson_id: int, score: int
    ) -> int:
        """Save student's test score."""
        # First get test_id for the lesson
        test_id = await self.db.fetchval(
            "SELECT id FROM tests WHERE lesson_id = $1", lesson_id
        )
        if not test_id:
            raise ValueError("No test found for this lesson")

        query = """
            INSERT INTO student_scores (
                student_id, 
                test_id, 
                score, 
                completed_at
            )
            VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
            RETURNING id
        """
        return await self.db.fetchval(query, student_id, test_id, score)

    async def get_student_highest_score(
        self, student_id: int, lesson_id: int
    ) -> Optional[Dict]:
        """
        Get student's highest score for a lesson's test.
        Returns dict with score and completion date, or None if no attempts.
        """
        query = """
            SELECT 
                s.score,
                s.completed_at
            FROM student_scores s
            JOIN tests t ON s.test_id = t.id
            WHERE s.student_id = $1 
            AND t.lesson_id = $2
            ORDER BY s.score DESC
            LIMIT 1
        """
        result = await self.db.fetchrow(query, student_id, lesson_id)
        return dict(result) if result else None
