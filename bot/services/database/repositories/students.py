from typing import Optional

from bot.services.database.models import Student


class StudentRepository:
    def __init__(self, db):
        self.db = db

    async def add_student(self, student_id: int, name: str, username: str):
        query = """
            INSERT INTO students (id, name, username)
            VALUES ($1, $2, $3)
            ON CONFLICT (id) DO NOTHING
        """

        return await self.db.execute(query, student_id, name, username)

    async def get_student(self, student_id: int) -> Optional[Student]:
        query = "SELECT * FROM students WHERE id = $1"
        result = await self.db.fetchrow(query, student_id)
        return Student(**result) if result else None
