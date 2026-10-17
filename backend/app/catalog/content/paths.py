"""Learning paths. Steps reference real course ids and lab ids."""
from __future__ import annotations


def _p(id, title, description, specialization, dmin, dmax, steps, tags=None):
    return dict(id=id, title=title, description=description,
                specialization=specialization, difficulty_min=dmin, difficulty_max=dmax,
                tags=tags or [], steps=steps)


def _s(order, course=None, lab=None, required=True, note=""):
    return dict(order=order, course_id=course, lab_id=lab, required=required, note=note)


LEARNING_PATHS = [
    _p("path-complete-beginner", "Complete Beginner",
       "Start from zero and build the foundations for every other path.",
       None, "orientation", "easy",
       [_s(1, "hacklab-orientation"), _s(2, "cybersecurity-fundamentals"),
        _s(3, "linux-fundamentals"), _s(4, "networking-fundamentals"),
        _s(5, "bash-for-security"), _s(6, "http-https"),
        _s(7, "service-enumeration"), _s(8, lab="web-security-lab", required=False,
                                         note="First easy security lab"),
        _s(9, "vulnerability-assessment"), _s(10, "security-reporting")],
       tags=["beginner", "foundation"]),

    _p("path-web-pentest", "Web Penetration Testing",
       "Progress from HTTP basics to chained web application assessment.",
       "web", "beginner", "expert",
       [_s(1, "http-https"), _s(2, "web-technologies"), _s(3, "linux-fundamentals"),
        _s(4, "sql-fundamentals"), _s(5, "authentication-security"),
        _s(6, "session-management-course"), _s(7, "access-control-course"),
        _s(8, "web-application-security"), _s(9, "sql-injection-labs"),
        _s(10, "cross-site-scripting"), _s(11, "api-security"),
        _s(12, lab="web-security-lab", note="Intermediate web lab"),
        _s(13, "advanced-web-security"),
        _s(14, "security-reporting", note="Final web assessment reporting")],
       tags=["web", "offensive"]),

    _p("path-infra-pentest", "Infrastructure Penetration Testing",
       "Network and host assessment across Linux and Windows.",
       "pentest", "beginner", "advanced",
       [_s(1, "networking-fundamentals"), _s(2, "linux-fundamentals"),
        _s(3, "windows-fundamentals"), _s(4, "dns-network-services"),
        _s(5, "reconnaissance"), _s(6, "service-enumeration"),
        _s(7, "vulnerability-assessment"), _s(8, "linux-privilege-escalation-concepts"),
        _s(9, "windows-privilege-escalation-concepts"),
        _s(10, lab="enterprise-identity-lab", note="Advanced multi-service lab"),
        _s(11, "security-reporting")],
       tags=["infrastructure", "offensive"]),

    _p("path-active-directory", "Active Directory Security",
       "Windows and directory services from fundamentals to identity security.",
       "active-directory", "beginner", "expert",
       [_s(1, "windows-fundamentals"), _s(2, "windows-administration"),
        _s(3, "authentication-security"), _s(4, "active-directory-fundamentals"),
        _s(5, "identity-access-management"),
        _s(6, "windows-privilege-escalation-concepts"),
        _s(7, lab="enterprise-identity-lab", note="Enterprise directory lab")],
       tags=["identity", "windows"]),

    _p("path-defensive", "Defensive Security",
       "Build blue-team skills from logging to incident response.",
       "defensive", "beginner", "advanced",
       [_s(1, "cybersecurity-fundamentals"), _s(2, "linux-administration"),
        _s(3, "windows-administration"), _s(4, "log-analysis"),
        _s(5, "network-monitoring"), _s(6, "siem-fundamentals"),
        _s(7, "detection-engineering"), _s(8, "threat-hunting"),
        _s(9, "incident-response"), _s(10, "digital-forensics"),
        _s(11, lab="defensive-monitoring-lab", note="Advanced investigation lab")],
       tags=["defensive", "blue-team"]),

    _p("path-reverse-engineering", "Reverse Engineering",
       "From programming foundations to binary analysis and memory safety.",
       "reverse", "easy", "expert",
       [_s(1, "bash-for-security"), _s(2, "python-for-security"),
        _s(3, "reverse-engineering-fundamentals"), _s(4, "memory-safety"),
        _s(5, "malware-analysis-fundamentals"),
        _s(6, lab="reverse-engineering-lab", note="Final RE challenge")],
       tags=["reverse", "re"]),

    _p("path-container-infra", "Container and Infrastructure Security",
       "Secure containers, orchestration and declarative infrastructure.",
       "cloud", "easy", "advanced",
       [_s(1, "linux-fundamentals"), _s(2, "linux-administration"),
        _s(3, "networking-fundamentals"), _s(4, "docker-security"),
        _s(5, "kubernetes-security"), _s(6, "network-segmentation"),
        _s(7, "iac-security"),
        _s(8, lab="container-security-lab", note="Advanced container lab")],
       tags=["cloud", "container"]),

    _p("path-digital-forensics", "Digital Forensics",
       "Evidence handling through incident reconstruction.",
       "forensics", "easy", "advanced",
       [_s(1, "log-analysis"), _s(2, "digital-forensics"),
        _s(3, "network-monitoring"), _s(4, "incident-response"),
        _s(5, "malware-analysis-fundamentals"),
        _s(6, lab="forensics-workstation-lab", note="Advanced investigation challenge")],
       tags=["forensics", "dfir"]),
]
