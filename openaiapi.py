import os
import base64
from openai import OpenAI
from dotenv import load_dotenv
from openai.types import skill
from openai.types.responses.container_auto_param import Skill
from pydantic import BaseModel, Field
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Session
import enum
import sqlalchemy

_ = load_dotenv()

client = OpenAI()


class Base(DeclarativeBase):
    pass


class SkillRankTable(Base):
    __tablename__ = "skill_rankings"

    user_id = sqlalchemy.Column("user_id", sqlalchemy.BLOB, primary_key=True)
    skills = sqlalchemy.Column("skills", sqlalchemy.JSON)
    done_processing = sqlalchemy.Column("done_processing", sqlalchemy.Boolean)


class SkillRanking(BaseModel):
    skill_name: str = Field(
        ...,
        description="Human-readable and distinct name representing a specific skill",
    )
    proficiency_level: int = Field(
        ...,
        le=4,
        ge=1,
        description="Numerical ranking of an applicant's proficiency in this skill from 1-4, where 1 is basic familiarity, 2 is extensive amateur experience, 3 is professional or academic experience, and 4 is proven, long-term mastery.",
    )


class SkillRankings(BaseModel):
    skills: list[SkillRanking] = Field(
        ..., description="All skills that the applicant has any experience with."
    )


def update_skill_db(user_id: bytes, engine: sqlalchemy.Engine, filename: str):
    skills = get_skills(filename)
    with Session(engine) as session:

        stmt = select(SkillRankTable).where(SkillRankTable.user_id == user_id)
        try:
            skill_ranking = session.scalars(stmt).one()
        except:
            return None

        if skills is None:
            skill_ranking.done_processing = True
            return
        else:
            skill_ranking.skills = skills.model_dump_json()
            skill_ranking.done_processing = True

        session.commit()


def get_skills(filename: str) -> SkillRankings | None:

    uploaded = client.files.create(file=open(filename, "rb"), purpose="assistants")
    response = client.responses.parse(
        model="gpt-5.2",
        instructions="You are an HR manager who is an expert in reading and parsing resumes. Determine what skills the applicant has from their PDF resume. Furthermore, rank their proficiency in each skill on a scale from 1-4, where 1 is basic familiarity, 2 is extensive amateur experience, 3 is professional or academic experience, and 4 is proven, long-term mastery.",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_file", "file_id": uploaded.id},
                ],
            }
        ],
        text_format=SkillRankings,
    )

    return response.output_parsed
