from typing import List, Optional

from asyncpg import Record

from bot.services.database.models import Topic


class TopicRepository:
    def __init__(self, db):
        self.db = db

    async def add_topic(self, title: str, description: str, class_number: int):
        query = """
            INSERT INTO topics (title, description, class)
            VALUES ($1, $2, $3)
        """
        return await self.db.execute(query, title, description, class_number)

    async def delete_topic(self, topic_id: int):
        query = "DELETE FROM topics WHERE id = $1"
        return await self.db.execute(query, topic_id)

    async def get_topic(self, topic_id: int) -> Optional[Topic]:
        query = "SELECT * FROM topics WHERE id = $1"
        result = await self.db.fetchrow(query, topic_id)
        return Topic(**result) if result else None

    async def get_topics_by_class(self, class_number: int) -> List[Topic]:
        query = "SELECT * FROM topics WHERE class = $1"
        rows: List[Record] = await self.db.fetch(query, class_number)
        return [Topic(**dict(row)) for row in rows]

    async def is_quiz_open(
        self, student_id: int, topic_id: int, min_lesson_score: int
    ) -> bool:
        """Returns whether a quiz for a topic is open for the student, only if all tests are passed."""
        query = """
            SELECT NOT EXISTS (
                -- Check if there is any test where the student didn't take it or failed it
                SELECT 1
                FROM topics t
                JOIN lessons l ON t.id = l.topic_id
                JOIN tests tst ON l.id = tst.lesson_id
                LEFT JOIN student_scores s ON tst.id = s.test_id AND s.student_id = $1
                WHERE t.id = $2
                GROUP BY tst.id
                HAVING MAX(s.score) IS NULL OR MAX(s.score) < $3
            ) AS all_tests_passed
        """

        result = await self.db.fetchrow(query, student_id, topic_id, min_lesson_score)

        # If there are no failed or missed tests, return True (all tests passed)
        return result["all_tests_passed"]
