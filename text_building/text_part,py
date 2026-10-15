
from dataclasses import dataclass, field


@dataclass 
class FullText:
    parts : list[TextPart] = field(default_factory=list)
    firstPart : TextPart 


#region Parts

@dataclass 
class TextPart:
    pass 


@dataclass 
class LinesPart(TextPart):
    lines : list[str] = field(default_factory=list)
    pass 

class Condition:
    pass 

@dataclass 
class ConditionPart(TextPart):
    conditions : list[Condition] = field(default_factory=list)


#endregion 
