from typing import List, TypedDict
from prisma import Prisma
from prisma.models import Skill, JobRole
from prisma.types import JobSkillCreateWithoutRelationsInput, JobRolesCreateWithoutRelationsInput

from api.gemini import generate_job_skills
from api.db import connect
from scraper.action import ScraperAction, ScraperItem
from scraper.config import ScraperActionConfig
from scraper.exception import ScraperException


class CustomConfig(ScraperActionConfig):
    frameworks: List[str]
    title_field: str
    description_field: str
    target_field: str
    min_skills: int

class SkillInfo(TypedDict):
    skill: str
    cluster: str

class JobInfo(TypedDict):
    titles: List[str]
    cluster: str
    industry: str

FAMILY = "gemini-2.0"

class ParseSkills(ScraperAction[CustomConfig]):
    uid = "jobiq.parse_skills"

    async def init(self):

        self.title_field = self.config["title_field"]
        self.description_field = self.config["description_field"]
        self.target_field = self.config["target_field"]
        self.min_skills = self.config["min_skills"]

    async def check_create_role(self, prisma: Prisma, jobs: JobInfo) -> JobRole:
        # check create industry
        industry = await prisma.industry.find_first(where={
            "OR": [
                { "name": jobs["industry"] },
                { "alternativeNames": { "has": jobs["industry"] } }
            ]
        })
        if industry is None:
            industry = await prisma.industry.create({
                "name": jobs["industry"]
            })

        # check create cluster
        cluster = await prisma.jobrole.find_first(where={
            "OR": [
                { "name": jobs["cluster"] },
                { "alternativeNames": { "has": jobs["cluster"] } }
            ], 
            "familyId": FAMILY
        })
        if cluster is None:
            cluster = await prisma.jobrole.create({
                "name": jobs["cluster"],
                "familyId": FAMILY,
                "industryId": industry.id
            })

        # find this role
        role = await prisma.jobrole.find_first(where={
            "OR": [
                { "name": { "in": jobs["titles"] } },
                { "alternativeNames": { "has_some": jobs["titles"] } }
            ],
            "parentId": cluster.id,
            "industryId": industry.id
        })

        # if role is found we merge the alternative names
        if role is None:
            role = await prisma.jobrole.create({
                "familyId": FAMILY,
                "name": jobs["titles"][0],
                "alternativeNames": jobs["titles"][1:],
                "parentId": cluster.id,
                "industryId":  industry.id
            })    
        # else:
        #     alternative_names = [*role.alternativeNames]
        #     for title in jobs["titles"]:
        #         if title != role.name and title not in alternative_names:
        #             alternative_names.append(title)
            
        #     if len(alternative_names) != len(role.alternativeNames):
        #         await prisma.jobrole.update(
        #             where={"id_familyId": {
        #                 "id": role.id, "familyId": FAMILY
        #             }},
        #             data={"alternativeNames": alternative_names}
        #         )

        return role

    async def check_create_skills(self, prisma: Prisma, skills: List[SkillInfo], skill_type: str, clusters: List[Skill]) -> List[Skill]:
        existing_skills = await prisma.skill.find_many(
            where={
                "OR": [
                    { "name": { "in": [x["skill"] for x in skills] } },
                    { "alternativeNames": { "has_some": [x["skill"] for x in skills] } }
                ],
                
                "type": skill_type,
                "familyId": FAMILY
            }
        )
        # Find missing competencies
        existing_skill_names = {name for c in existing_skills for name in [c.name, *(c.alternativeNames or [])]}   
        all_competency_names = {x["skill"] for x in skills}
        missing_skills = all_competency_names - existing_skill_names

        # Insert missing competencies
        new_skills: List[Skill] = []
        for skill in [x for x in skills if x["skill"] in missing_skills]:
            # Find the cluster in clusters by name
            cluster = next((c for c in clusters if c.name == skill["cluster"]), None)
            competency = await prisma.skill.create(
                {
                    "name": skill["skill"],
                    "familyId": FAMILY,
                    "parentSkillId": cluster.id if cluster else None,
                    "type": skill_type,
                }
            )
            new_skills.append(competency)

        # Create a new array with all competencies (existing + newly inserted)
        return list(existing_skills) + new_skills
    
    async def check_create_clusters_and_skills(self, prisma: Prisma, skills: List[SkillInfo], skill_type: str) -> List[Skill]:
        unique_clusters = list({x["cluster"] for x in skills})
        clusters = await self.check_create_skills(
            prisma,
            [{"skill": cluster, "cluster": ""} for cluster in unique_clusters],
            "cluster",
            []
        )
        return await self.check_create_skills(prisma, skills, skill_type, clusters)

    async def _execute(self, scraper: ScraperItem):
        item = scraper.item
        skill_mappings: List[JobSkillCreateWithoutRelationsInput] = []

        title = item[self.title_field] if self.title_field in item else ""
        description = item[self.description_field] if self.description_field in item else ""

        # for each framework add those skills
        result = generate_job_skills(
            title,
            description
        )

        if result is None:
            raise ScraperException(
                "error", f"No response when generating skills for '{title}'")

        prisma = await connect()

        competencies: List[Skill] = await self.check_create_clusters_and_skills(
            prisma,
            [{ 
                "cluster": x["cluster"],
                "skill": x["competency"]
            } for x in result["core_competencies"]],
            "competency"
        )
        
        technologies = await self.check_create_clusters_and_skills(
            prisma,
            [{ 
                "cluster": x["cluster"],
                "skill": x["tool"]
            } for x in result["technology_tools"]],
            "tool"
        )
        
        tasks = await self.check_create_clusters_and_skills(
            prisma,
            [{ 
                "cluster": x["cluster"],
                "skill": x["task"]
            } for x in result["specialist_tasks"]],
            "task"
        ) 

        for skill in competencies + technologies + tasks:
            skill_mappings.append(
                {
                    "skillFamilyId": FAMILY,
                    "skillId": skill.id,
                }
            )
        

        # for core_competency in result["core_competencies"]:
            
        role = await self.check_create_role(
            prisma,
            {
                "titles": result["job_titles"],
                "cluster": result["job_cluster"],
                "industry": result["industry"]
            }
        )

        jobRole: JobRolesCreateWithoutRelationsInput = {
            "roleId": role.id,
            "familyId": FAMILY
        }

        # set the skill mappings
        item[self.target_field] = {
            "Skills": skill_mappings,
            "Role": jobRole
        }
