import operator
from typing import Annotated
from typing_extensions import TypedDict

class Section (TypedDict):
    id: int
    title: str
    description: str
    queries: list[str]

class Brief (TypedDict):
    section_id: int
    section_title: str
    findings: str
    sources: list[str]

class ResearchState (TypedDict):
    user_message: str
    input_type: str
    topic: str
    sections: list[Section]
    briefs: Annotated[list[Brief], operator.add]
    report: str
    output: str
    