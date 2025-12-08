from pydantic import BaseModel
from typing import List, Optional, Dict

class Paper(BaseModel):
    paperId: Optional[str]
    title: str
    abstract: Optional[str]
    authors: List[str] = []
    url: Optional[str]
    year: Optional[int]
    venue: Optional[str]
    publicationTypes: List[str] = []
    citationCount: Optional[int]
    referenceCount: Optional[int]
    referencedWorks: List[str] = []  # OpenAlex IDs of papers this paper references
    isOpenAccess: Optional[bool]
    openAccessPdf: Optional[str]
    externalIds: Dict = {}
    fieldsOfStudy: List[str] = []
    source: Optional[str]
    topic: Optional[str]
    content: Optional[str]
