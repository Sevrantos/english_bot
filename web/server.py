import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from bot.services.database.connection import Database
from bot.utils import config


async def lifespan(app: FastAPI):
    app.state.db = Database(config.DSN)
    await app.state.db.connect()
    yield
    await app.state.db.disconnect()


app = FastAPI(lifespan=lifespan)


class Score(BaseModel):
    id: int
    score: int
    completed_at: str


class LessonDetails(BaseModel):
    lesson_id: int
    title: str
    score: Score


class TopicDetails(BaseModel):
    topic_id: int
    title: str
    lessons: List[LessonDetails]
    quiz_score: Optional[Score] = None


class ClassDetails(BaseModel):
    class_number: int
    topics: List[TopicDetails]


class StudentScoresResponse(BaseModel):
    student_id: int
    name: str
    username: str
    classes: List[ClassDetails]

    class Config:
        from_attributes = True


def get_db():
    if not hasattr(app.state, "db"):
        raise HTTPException(
            status_code=500, detail="Database connection is not initialized"
        )
    return app.state.db


@app.get("/students/{student_id}/scores", response_model=StudentScoresResponse)
async def get_student_scores(student_id: int, db: Database = Depends(get_db)):
    async with db.pool.acquire() as connection:
        student = await connection.fetchrow(
            "SELECT id, name, username FROM students WHERE id = $1", student_id
        )
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")


        lesson_scores = await connection.fetch(
            """
            WITH RankedLessonScores AS (
                SELECT 
                    tp.class,
                    tp.id AS topic_id, 
                    tp.title AS topic_title, 
                    l.id AS lesson_id, 
                    l.title AS lesson_title, 
                    ss.id AS score_id, 
                    ss.score, 
                    ss.completed_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY l.id
                        ORDER BY ss.score DESC, ss.completed_at DESC
                    ) as rank
                FROM student_scores ss
                JOIN tests ts ON ss.test_id = ts.id
                JOIN lessons l ON ts.lesson_id = l.id
                JOIN topics tp ON l.topic_id = tp.id
                WHERE ss.student_id = $1
            )
            SELECT *
            FROM RankedLessonScores
            WHERE rank = 1
            """,
            student_id,
        )


        quiz_scores = await connection.fetch(
            """
            WITH RankedQuizScores AS (
                SELECT 
                    tp.class,
                    tp.id AS topic_id, 
                    tp.title AS topic_title, 
                    ss.id AS score_id, 
                    ss.score, 
                    ss.completed_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY q.topic_id
                        ORDER BY ss.score DESC, ss.completed_at DESC
                    ) as rank
                FROM student_scores ss
                JOIN quizzes q ON ss.quiz_id = q.id
                JOIN topics tp ON q.topic_id = tp.id
                WHERE ss.student_id = $1
            )
            SELECT *
            FROM RankedQuizScores
            WHERE rank = 1
            """,
            student_id,
        )


        classes = {}


        for row in lesson_scores:
            class_number = row["class"]
            topic_id = row["topic_id"]
            topic_title = row["topic_title"]
            lesson_id = row["lesson_id"]
            lesson_title = row["lesson_title"]
            score_id = row["score_id"]
            score_val = row["score"]
            completed_at = (
                row["completed_at"].isoformat() if row["completed_at"] else None
            )

            if class_number not in classes:
                classes[class_number] = {}
            class_data = classes[class_number]

            if topic_id not in class_data:
                class_data[topic_id] = {
                    "title": topic_title,
                    "lessons": {},
                    "quiz_score": None,
                }
            topic_data = class_data[topic_id]


            if lesson_id not in topic_data["lessons"]:
                topic_data["lessons"][lesson_id] = {
                    "lesson_id": lesson_id,
                    "title": lesson_title,
                    "score": None,
                }
            lesson_data = topic_data["lessons"][lesson_id]


            lesson_data["score"] = {
                "id": score_id,
                "score": score_val,
                "completed_at": completed_at,
            }


        for row in quiz_scores:
            class_number = row["class"]
            topic_id = row["topic_id"]
            topic_title = row["topic_title"]
            score_id = row["score_id"]
            score_val = row["score"]
            completed_at = (
                row["completed_at"].isoformat() if row["completed_at"] else None
            )

            if class_number not in classes:
                classes[class_number] = {}
            class_data = classes[class_number]

            if topic_id not in class_data:
                class_data[topic_id] = {
                    "title": topic_title,
                    "lessons": {},
                    "quiz_score": None,
                }
            topic_data = class_data[topic_id]

            topic_data["quiz_score"] = {
                "id": score_id,
                "score": score_val,
                "completed_at": completed_at,
            }


        student_scores = StudentScoresResponse(
            student_id=student["id"],
            name=student["name"],
            username=student["username"],
            classes=[],
        )

        for class_number in sorted(classes.keys()):
            class_details = ClassDetails(class_number=class_number, topics=[])

            for topic_id, topic_info in sorted(classes[class_number].items()):

                lessons = []
                for lesson_id, lesson_info in sorted(topic_info["lessons"].items()):
                    if lesson_info["score"]:
                        lesson_score = Score(**lesson_info["score"])
                        lessons.append(
                            LessonDetails(
                                lesson_id=lesson_id,
                                title=lesson_info["title"],
                                score=lesson_score,
                            )
                        )

                quiz_score = None
                if topic_info["quiz_score"]:
                    quiz_score = Score(**topic_info["quiz_score"])

                topic_details = TopicDetails(
                    topic_id=topic_id,
                    title=topic_info["title"],
                    lessons=lessons,
                    quiz_score=quiz_score,
                )
                class_details.topics.append(topic_details)

            student_scores.classes.append(class_details)

        return student_scores


static_directory = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=static_directory, html=True), name="static")

if not os.path.exists(static_directory):
    os.makedirs(static_directory)
