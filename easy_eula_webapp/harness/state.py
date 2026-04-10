from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class AnalysisState:
    """Shared state container for the analysis workflow."""
    urls: List[str] = field(default_factory=list)
    raw_texts: Dict[str, str] = field(default_factory=dict)
    
    # Analysis outputs
    summary: Optional[str] = None
    impact: Optional[str] = None
    tinfoil: Optional[str] = None
    
    # Optional diagnostics/status
    diagnostics: List[str] = field(default_factory=list)
