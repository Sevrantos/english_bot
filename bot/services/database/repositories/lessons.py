from typing import List, Optional

from asyncpg import Record

from bot.services.database.models import Lesson, Material


class LessonRepository:
    def __init__(self, db):
        self.db = db

    async def add_lesson(self, title: str, description: str, topic_id: int):
        query = """
            INSERT INTO lessons (title, description, topic_id)
            VALUES ($1, $2, $3)
        """
        return await self.db.execute(query, title, description, topic_id)

    async def delete_lesson(self, lesson_id: int):
        query = "DELETE FROM lessons WHERE id = $1"
        return await self.db.execute(query, lesson_id)

    async def get_lessson(self, lesson_id: int) -> Optional[Lesson]:
        query = "SELECT * FROM lessons WHERE id = $1"
        result = await self.db.fetchrow(query, lesson_id)
        return Lesson(**result) if result else None

    async def get_class_by_lesson(self, lesson_id: int) -> int:
        query = """
            SELECT class
            FROM topics
            JOIN lessons ON topics.id = lessons.topic_id
            WHERE lessons.id = $1
        """
        return await self.db.fetchval(query, lesson_id)

    async def get_lessons_by_topic(self, topic_id: int) -> List[Lesson]:
        query = "SELECT * FROM lessons WHERE topic_id = $1"
        rows: List[Record] = await self.db.fetch(query, topic_id)
        return [Lesson(**dict(row)) for row in rows]

    async def add_material(self, lesson_id: int, file_id: str, file_type: str):
        query = """
            INSERT INTO materials (lesson_id, file_id, type)
            VALUES ($1, $2, $3)
        """
        return await self.db.execute(query, lesson_id, file_id, file_type)

    async def get_materials(self, lesson_id: int) -> List[Material]:
        query = "SELECT * FROM materials WHERE lesson_id = $1"
        rows: List[Record] = await self.db.fetch(query, lesson_id)
        return [Material(**dict(row)) for row in rows]

    async def delete_materials(self, lesson_id: int):
        query = "DELETE FROM materials WHERE lesson_id = $1"
        return await self.db.execute(query, lesson_id)
