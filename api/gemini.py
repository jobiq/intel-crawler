# To run this code you need to install the following dependencies:
# pip install google-genai

#type: ignore

import os
from typing import Literal
from google import genai
from google.genai import types

from api.types import JobSchema
import json

def skill_schema_json():
    # Read the skill schema JSON file
    with open("skill_schema.json", "r", encoding="utf-8") as f:
        skill_schema_json = f.read()
    return skill_schema_json

skill_schema = skill_schema_json()

def generate(query: str, schema_source: Literal["job"] ):
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    schema = skill_schema if schema_source == "job" else None

    model = "gemini-2.0-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=query),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=genai.types.Schema(
            type = genai.types.Type.OBJECT,
            required = ["core_competencies", "specialist_tasks", "job_titles", "industry", "education"],
            properties = {
                "job_cluster": genai.types.Schema(
                    type = genai.types.Type.STRING,
                    description = "The job role cluster this job belongs to. For example, 'Software Development' or 'Accounting and Audit'.",
                ),
                "job_titles": genai.types.Schema(
                    type = genai.types.Type.ARRAY,
                    description = "The job titles for this job",
                    items = genai.types.Schema(
                        type = genai.types.Type.STRING,
                        description = "Job title for this job and some synonyms. For example, 'Software Engineer', 'Software Developer', 'Programmer'.",
                    ),
                ),
                "industry": genai.types.Schema(
                    type = genai.types.Type.STRING,
                    description = "The industry this job belongs to. For example, 'Information Technology, or Business'.",
                ),
                "education": genai.types.Schema(
                    type = genai.types.Type.STRING,
                    description = "The education level required for this job. For example, 'Bachelor's degree'.",
                ),
                "core_competencies": genai.types.Schema(
                    type = genai.types.Type.ARRAY,
                    description = "Find the core competencies that this job requires? Core competencies are skills that are common to all jobs such as ‘teamwork’ or ‘problem solving’. They are sometimes known as ‘foundation skills’ or ‘employability skills’. The core competencies in the Australian Skills Classification align to the definitions of foundation skills typically used in the Australian VET system – specifically the Employability Skills Framework developed by the Australian Skills Quality Authority with minor differences recommended by education system experts. Try to find at least 5 covered and 3 missing, but more the better.",
                    items = genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        required = ["competency", "level", "cluster"],
                        properties = {
                            "competency": genai.types.Schema(
                                type = genai.types.Type.STRING,
                                description = "The name of the competency.",
                            ),
                            "level": genai.types.Schema(
                                type = genai.types.Type.NUMBER,
                                description = "The level of expertise acquired. Use 0 for beginner, being able to follow instructions. 1 for intermediate, being able to work independently and apply skill to new problems. 3 for master, being able to work independently, educate others and lead activities requiring this skill.",
                            ),
                            "cluster": genai.types.Schema(
                                type = genai.types.Type.STRING,
                                description = "What is the topmost cluster this competency belongs to? For example, 'Interpersonal Skills'.",
                                enum = ["navigating the world of work", "interacting with others", "getting the work done"],
                            ),
                        },
                    ),
                ),
                "specialist_tasks": genai.types.Schema(
                    type = genai.types.Type.ARRAY,
                    description = "Which specialist tasks are covered or missing in subject? To find missing tasks consider the jobs that this subject supports and the tasks those jobs require, yet are not taught in this subject but should be. Try to find at least 15 covered and 15 missing. Specialist tasks these are the activities that describe day-to-day work in a job – for example ‘preparing financial documents’ or ‘giving immunisations’. While specialist tasks can be transferrable across occupations and sectors, they are not universal - unlike core competencies. As such, specialist tasks are useful for differentiating occupations. Specialist tasks change more frequently than core competencies, making it possible to identify trends. This information adds to our understanding of how jobs may be changing in response to factors like increased digitisation or changing business models. Industry and employers can use the specialist tasks to define critical skills and identify skill gaps that could be met by learning on the job, short courses or accelerated training. Try to find at least 5 covered and 3 missing, but more the better.",
                    items = genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        required = ["task", "level", "cluster"],
                        properties = {
                            "task": genai.types.Schema(
                                type = genai.types.Type.STRING,
                                description = "The name of the soft task.",
                            ),
                            "level": genai.types.Schema(
                                type = genai.types.Type.NUMBER,
                                description = "The level of expertise acquired. Use 0 for beginner, being able to follow instructions. 1 for intermediate, being able to work independently and apply skill to new problems. 3 for master, being able to work independently, educate others and lead activities requiring this skill.",
                            ),
                            "cluster": genai.types.Schema(
                                type = genai.types.Type.STRING,
                                description = "What would be highest level cluster this task would belong to. Think of cluster as a group of tasks that are related to each other. For example, 'Programming'. A cluster should include at least 10 to 15 different skills",
                            ),
                        },
                    ),
                ),
                "technology_tools": genai.types.Schema(
                    type = genai.types.Type.ARRAY,
                    description = "Extract all technology tools are taught or missing in subject? To find missing tools consider the jobs that this subject supports and the tools those jobs require to use, yet are not taught in this subject but should be. Try to extract at least 5 taught and 3 missing. Technology tools are the software and hardware used in occupations – for example ‘graphics or photo imaging software’. The technology tools describe software and equipment types or categories and provide specific packages or products as examples. Understanding the technology tools required in occupations, and how these are changing, can help inform decisions about training, up-skilling and re-skilling, or how to take advantage of emerging technologies across different fields and industries. Try to find at least 5 covered and 3 missing, but more the better.",
                    items = genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        required = ["tool", "level", "cluster"],
                        properties = {
                            "tool": genai.types.Schema(
                                type = genai.types.Type.STRING,
                                description = "The name of the tool.",
                            ),
                            "level": genai.types.Schema(
                                type = genai.types.Type.NUMBER,
                                description = "The level of expertise acquired. Use 0 for beginner, being able to follow instructions. 1 for intermediate, being able to work independently and apply skill to new problems. 3 for master, being able to work independently, educate others and lead activities requiring this skill.",
                            ),
                            "cluster": genai.types.Schema(
                                type = genai.types.Type.STRING,
                                description = "What would be highest level cluster this tool would belong to. Think of cluster as a group of tools that are related to each other. For example, 'Office Software', or 'Graphic Software'. A cluster should include at least 10 to 15 different tools",
                            ),
                        },
                    ),
                ),
            },
        ),
    )

    result = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    ).text

    # print("Result: ", result)
    return result


def generate_job_skills(job_title: str, job_description: str) -> JobSchema | None:
    query = f"Title: '{job_title}'\nDescription:\n{job_description}" 
    response = generate(query, schema_source="job")
    return json.loads(response) if response else None
