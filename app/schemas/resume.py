from pydantic import BaseModel
from typing import Optional


class ExperienceSchema(BaseModel):
    company: str
    role: Optional[str] = None
    employment_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


class EducationSchema(BaseModel):
    school: str
    degree: Optional[str] = None
    major: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[str] = None


class ProjectSchema(BaseModel):
    name: str
    description: Optional[str] = None
    role: Optional[str] = None
    tech_stack: list[str] = []
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    url: Optional[str] = None


class CertificationSchema(BaseModel):
    name: str
    issuer: Optional[str] = None
    date: Optional[str] = None
    grade: Optional[str] = None


class LanguageSchema(BaseModel):
    language: str
    test: Optional[str] = None
    score: Optional[str] = None
    date: Optional[str] = None


class ActivitySchema(BaseModel):
    type: Optional[str] = None
    name: str
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


class AwardSchema(BaseModel):
    name: str
    issuer: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None


class MilitarySchema(BaseModel):
    status: Optional[str] = None
    branch: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class OverseasExperienceSchema(BaseModel):
    country: str
    purpose: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class DisabilitySchema(BaseModel):
    status: bool = False
    detail: Optional[str] = None


class ResumeStructured(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[str] = None
    location: Optional[str] = None
    github: Optional[str] = None
    blog: Optional[str] = None
    summary: Optional[str] = None
    skills: list[str] = []
    experience: list[ExperienceSchema] = []
    education: list[EducationSchema] = []
    projects: list[ProjectSchema] = []
    certifications: list[CertificationSchema] = []
    languages: list[LanguageSchema] = []
    activities: list[ActivitySchema] = []
    awards: list[AwardSchema] = []
    military: Optional[MilitarySchema] = None


class ResumeProcessResponse(BaseModel):
    status: str
    user_id: str
    structured_data: ResumeStructured
    desired_job: Optional[str] = None
    linkedin: Optional[str] = None
    overseas_experience: list[OverseasExperienceSchema] = []
    disability: Optional[DisabilitySchema] = None
    driving_license: Optional[str] = None
