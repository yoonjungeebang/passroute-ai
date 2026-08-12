
from pydantic import BaseModel


class ExperienceSchema(BaseModel):
    company: str
    role: str | None = None
    employment_type: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None


class EducationSchema(BaseModel):
    school: str
    degree: str | None = None
    major: str | None = None
    status: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    gpa: str | None = None


class ProjectSchema(BaseModel):
    name: str
    description: str | None = None
    role: str | None = None
    tech_stack: list[str] = []
    start_date: str | None = None
    end_date: str | None = None
    url: str | None = None


class CertificationSchema(BaseModel):
    name: str
    issuer: str | None = None
    date: str | None = None
    grade: str | None = None


class LanguageSchema(BaseModel):
    language: str
    test: str | None = None
    score: str | None = None
    date: str | None = None


class ActivitySchema(BaseModel):
    type: str | None = None
    name: str
    role: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None


class AwardSchema(BaseModel):
    name: str
    issuer: str | None = None
    date: str | None = None
    description: str | None = None


class MilitarySchema(BaseModel):
    status: str | None = None
    branch: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class OverseasExperienceSchema(BaseModel):
    country: str
    purpose: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class DisabilitySchema(BaseModel):
    status: bool = False
    detail: str | None = None

class ResumeStructured(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    birth_date: str | None = None
    location: str | None = None
    github: str | None = None
    blog: str | None = None
    summary: str | None = None
    skills: list[str] = []
    experience: list[ExperienceSchema] = []
    education: list[EducationSchema] = []
    projects: list[ProjectSchema] = []
    certifications: list[CertificationSchema] = []
    languages: list[LanguageSchema] = []
    activities: list[ActivitySchema] = []
    awards: list[AwardSchema] = []
    military: MilitarySchema | None = None


class ResumeProcessResponse(BaseModel):
    status: str
    user_id: str
    structured_data: ResumeStructured
    desired_job: str | None = None
    linkedin: str | None = None
    overseas_experience: list[OverseasExperienceSchema] = []
    disability: DisabilitySchema | None = None
    driving_license: str | None = None
