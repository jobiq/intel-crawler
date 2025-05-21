from typing import TypedDict, List, Literal

# Reusable Enums
ProficiencyLevel = Literal["1", "2", "3", "4"]
StatusType = Literal["required", "optional", "assumed"]

# Sub-Objects
class Competency(TypedDict):
    competency: str
    level: ProficiencyLevel
    status: StatusType
    cluster: str

class SpecialistTask(TypedDict):
    task: str
    level: ProficiencyLevel
    status: StatusType
    cluster: str

class TechnologyTool(TypedDict):
    tool: str
    level: ProficiencyLevel
    status: StatusType
    cluster: str

# Main Object
class JobSchema(TypedDict):
    job_titles: List[str]
    job_cluster: str
    industry: str
    education: str
    core_competencies: List[Competency]
    specialist_tasks: List[SpecialistTask]
    technology_tools: List[TechnologyTool]