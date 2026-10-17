"""Web and application security courses (defensive/educational framing)."""
from __future__ import annotations

from backend.app.catalog.content._authoring import (
    assessment, course, cmd, lesson, mcq, short,
)


def _c(id, title, desc, difficulty, prereqs, lessons, qs, cprereqs=None,
       tags=None, lab=None, spec="web"):
    return course(id, title, desc, difficulty, "web-security", specialization=spec,
                  prerequisites=prereqs, competency_prereqs=cprereqs or [],
                  tags=tags or ["web"], lab_id=lab, lessons=lessons,
                  assessment=assessment(f"{title} Assessment", qs, difficulty))


L = lesson
COURSES = [
    _c("web-technologies", "Web Technologies",
       "HTML, JavaScript, cookies and the browser security model.",
       "beginner", ["cybersecurity-fundamentals"],
       [L("How the web fits together", "beginner", 15, "web-technologies",
          "A browser requests resources over HTTP(S); servers return HTML, CSS and "
          "JavaScript. The browser enforces the **same-origin policy**: scripts from "
          "one origin cannot freely read another origin's data. Cookies carry state "
          "(including sessions). Understanding origins, cookies and how the browser "
          "isolates sites is the foundation of all web security.",
          exercises=[mcq("The same-origin policy restricts:",
                         ["CSS loading", "Cross-origin script data access",
                          "Image sizes", "Cookie expiry"],
                         "Cross-origin script data access", "web-technologies",
                         "SOP stops scripts reading another origin's data.")],
          hints=["Origin = scheme + host + port."]),
        L("Cookies and state", "beginner", 15, "session-management",
          "HTTP is stateless, so applications track users with cookies. Security "
          "attributes matter: `Secure` (HTTPS only), `HttpOnly` (not readable by JS), "
          "and `SameSite` (limits cross-site sending). Session cookies should set all "
          "three appropriately to resist theft and cross-site request forgery.",
          exercises=[short("Cookie attribute that hides it from JavaScript?", "HttpOnly",
                           "session-management", "HttpOnly blocks JS access to the cookie.")])],
       [mcq("Which cookie flag limits cross-site sending?",
            ["Secure", "HttpOnly", "SameSite", "Path"], "SameSite", "session-management",
            "SameSite controls cross-site cookie sending."),
        short("scheme+host+port defines an ___", "origin", "web-technologies",
              "That triple is the origin.")]),

    _c("http-https", "HTTP and HTTPS",
       "Requests, responses, status codes, headers and transport security.",
       "beginner", ["web-technologies"],
       [L("Anatomy of a request", "beginner", 15, "http-fundamentals",
          "An HTTP request has a method (GET, POST, PUT, DELETE), a path, headers and "
          "an optional body. Responses carry a status code (2xx success, 3xx redirect, "
          "4xx client error, 5xx server error) and headers. Methods have semantics: GET "
          "should not change state. Reading requests/responses precisely is essential.",
          exercises=[mcq("Which status class means client error?",
                         ["2xx", "3xx", "4xx", "5xx"], "4xx", "http-fundamentals",
                         "4xx indicates client-side errors.")],
          hints=["GET is safe/idempotent; POST changes state."]),
        L("Security headers and HTTPS", "beginner", 15, "tls-certificates",
          "HTTPS (TLS) provides confidentiality and integrity in transit and "
          "authenticates the server via certificates. Response headers harden the app: "
          "`Content-Security-Policy`, `Strict-Transport-Security`, `X-Content-Type-"
          "Options`, and `X-Frame-Options`. These are cheap, high-value defensive "
          "controls.",
          exercises=[short("Header that forces HTTPS for future visits? (acronym)", "HSTS",
                           "tls-certificates", "Strict-Transport-Security is HSTS.")])],
       [mcq("500-series status codes indicate:",
            ["Success", "Redirect", "Client error", "Server error"], "Server error",
            "http-fundamentals", "5xx are server errors."),
        short("Header defining allowed script sources? (acronym)", "CSP",
              "web-technologies", "Content-Security-Policy is CSP.")]),

    _c("web-application-security", "Web Application Security",
       "The common classes of web vulnerability and how to prevent them.",
       "intermediate", ["http-https"],
       [L("Trust boundaries and input", "intermediate", 20, "input-validation",
          "Most web vulnerabilities come from mixing untrusted input with a trusted "
          "context. The defensive mental model: identify every trust boundary (user → "
          "app, app → database, app → OS, app → browser) and ensure data is validated "
          "on input and correctly encoded for each output context. This single idea "
          "underlies SQLi, XSS, command injection and more.",
          exercises=[mcq("The root cause of injection flaws is:",
                         ["Slow servers", "Mixing untrusted data with a trusted context",
                          "Too many headers", "Weak CPUs"],
                         "Mixing untrusted data with a trusted context", "input-validation",
                         "Injection arises when data crosses into a command/markup context.")],
          hints=["Validate on input, encode on output — for the specific context."]),
        L("The OWASP Top 10 mindset", "intermediate", 15, "vuln-assessment",
          "The OWASP Top 10 catalogues prevalent risks: broken access control, "
          "cryptographic failures, injection, insecure design, misconfiguration, and "
          "more. Treat it as a checklist for review, not a guarantee. For each category, "
          "learn the defensive control: parameterised queries, output encoding, strong "
          "authz checks, secure defaults.",
          exercises=[short("OWASP risk category for missing authorisation checks? (broken ___ control)",
                           "access", "access-control", "Broken access control.")])],
       [mcq("Best defence against injection generally?",
            ["Disable logs", "Context-correct encoding and parameterisation",
             "Hide errors", "Use GET only"], "Context-correct encoding and parameterisation",
            "input-validation", "Separate data from code via parameterisation/encoding."),
        short("Encode output for the ___ it enters (context).", "context",
              "input-validation", "Encode per output context.")],
       cprereqs=["http-fundamentals"], lab="web-security-lab"),

    _c("sql-fundamentals", "SQL Fundamentals",
       "Relational data, queries and why parameterisation matters.",
       "easy", ["linux-fundamentals"],
       [L("SELECT, WHERE, JOIN", "easy", 15, "input-validation",
          "SQL queries relational tables. `SELECT col FROM users WHERE id = 5` returns "
          "rows; `JOIN` combines tables on a key. Understanding how queries are built is "
          "necessary to understand how *string-built* queries become injectable and how "
          "*parameterised* queries stay safe.",
          exercises=[mcq("Which clause filters rows?",
                         ["SELECT", "FROM", "WHERE", "ORDER BY"], "WHERE", "input-validation",
                         "WHERE filters rows.")]),
        L("Parameterised queries", "easy", 15, "sql-injection",
          "A parameterised (prepared) query sends SQL and data separately, so user input "
          "can never change query structure. This is the definitive defence against SQL "
          "injection. Building queries by string concatenation is the anti-pattern that "
          "creates the vulnerability.",
          exercises=[mcq("The definitive defence against SQL injection is:",
                         ["Escaping quotes by hand", "Parameterised queries",
                          "Hiding the DB", "Rate limiting"], "Parameterised queries",
                         "sql-injection", "Prepared statements separate code from data.")],
          hints=["If input can change query structure, it is unsafe."])],
       [short("Clause that filters rows in SQL?", "WHERE", "input-validation",
              "WHERE filters."),
        mcq("String-concatenated SQL is dangerous because input can:",
            ["Slow the DB", "Alter query structure", "Add indexes", "Change charset"],
            "Alter query structure", "sql-injection", "Concatenation lets input change the query.")]),

    _c("sql-injection-labs", "SQL Injection in Isolated Labs",
       "Recognise, verify and remediate SQL injection in a safe lab.",
       "intermediate", ["sql-fundamentals", "web-application-security"],
       [L("Recognising injection", "intermediate", 20, "sql-injection",
          "SQL injection occurs when untrusted input alters a query's structure. "
          "Symptoms a defender looks for: error messages revealing SQL, behaviour that "
          "changes with quote characters, and unexpected data returned. In the lab you "
          "will observe how a vulnerable endpoint differs from a parameterised one, then "
          "apply the fix and confirm the behaviour is gone.",
          exercises=[mcq("A reliable fix once SQLi is found:",
                         ["Blocklist the word SELECT", "Convert to parameterised queries",
                          "Lowercase input", "Add a CAPTCHA"],
                         "Convert to parameterised queries", "sql-injection",
                         "Parameterisation removes the class of bug.")],
          hints=["Compare the vulnerable and fixed endpoints side by side."]),
        L("Verifying the remediation", "intermediate", 15, "vuln-remediation",
          "Finding a bug is half the job; proving it is fixed is the other half. After "
          "converting to prepared statements, re-test the same inputs and confirm the "
          "query structure cannot change. Document the before/after for the report — a "
          "core professional skill.",
          exercises=[short("Prepared statements separate code from ___.", "data",
                           "sql-injection", "They separate SQL code from data.")])],
       [mcq("SQLi root cause:", ["Weak CPU", "Input altering query structure",
            "Large tables", "UDP"], "Input altering query structure", "sql-injection",
            "Input changing the query is the cause."),
        short("What you produce to show a fix works (before/___)?", "after",
              "vuln-remediation", "Before/after evidence.")],
       cprereqs=["sql-injection"], lab="web-security-lab"),

    _c("cross-site-scripting", "Cross-Site Scripting",
       "How XSS arises in the browser and how output encoding prevents it.",
       "intermediate", ["web-application-security"],
       [L("Reflected, stored and DOM XSS", "intermediate", 20, "xss",
          "XSS happens when an application places untrusted data into a page without "
          "correct encoding, so the browser treats it as script. Variants: reflected "
          "(from the request), stored (persisted server-side) and DOM-based (client-side "
          "sink). The defence is context-aware output encoding plus a Content-Security-"
          "Policy as defence in depth.",
          exercises=[mcq("Primary defence against XSS:",
                         ["Input length limits", "Context-aware output encoding",
                          "Faster rendering", "UDP"], "Context-aware output encoding",
                         "xss", "Encoding for the output context neutralises markup.")],
          hints=["Encode for HTML, attribute, JS or URL context specifically."]),
        L("Content-Security-Policy", "intermediate", 15, "web-technologies",
          "A strong CSP restricts where scripts may load from and can block inline "
          "script, greatly reducing XSS impact even if an encoding bug slips through. "
          "It is defence in depth, not a substitute for correct encoding.",
          exercises=[short("Header that restricts script sources? (acronym)", "CSP",
                           "web-technologies", "Content-Security-Policy.")])],
       [mcq("Stored XSS differs from reflected because the payload is:",
            ["In the URL only", "Persisted server-side", "In a cookie", "In DNS"],
            "Persisted server-side", "xss", "Stored XSS is saved and served to others."),
        short("Defence in depth header for XSS? (acronym)", "CSP", "web-technologies",
              "CSP adds a second layer.")],
       cprereqs=["input-validation"], lab="web-security-lab"),

    _c("authentication-security", "Authentication Security",
       "Password handling, MFA and common authentication weaknesses.",
       "intermediate", ["http-https"],
       [L("Storing credentials", "intermediate", 15, "authn-security",
          "Passwords must be stored as salted, slow hashes (bcrypt, scrypt, Argon2) — "
          "never plaintext or fast hashes like raw SHA-256. Salting defeats precomputed "
          "tables; a slow algorithm defeats brute force. Pwnforge itself uses Argon2id for "
          "exactly this reason.",
          exercises=[mcq("Which is appropriate for password storage?",
                         ["MD5", "Plain SHA-256", "Argon2id", "Base64"], "Argon2id",
                         "authn-security", "Argon2id is a slow, salted KDF.")],
          hints=["Fast hashes are wrong for passwords."]),
        L("MFA and lockout", "intermediate", 15, "authn-security",
          "Multi-factor authentication adds a second factor so a stolen password is not "
          "enough. Rate limiting and lockout slow credential-guessing. Generic error "
          "messages avoid revealing whether a username exists. Together these harden the "
          "login flow.",
          exercises=[short("A second authentication factor is called ___ (acronym).", "MFA",
                           "authn-security", "Multi-factor authentication.")])],
       [mcq("Best password storage choice:", ["SHA-1", "Argon2id", "ROT13", "CRC32"],
            "Argon2id", "authn-security", "Argon2id is a modern password KDF."),
        short("Control that slows online guessing?", "rate limiting", "authn-security",
              "Rate limiting slows guessing.")]),

    _c("session-management-course", "Session Management",
       "Session lifecycle, fixation, and secure cookie handling.",
       "intermediate", ["authentication-security"],
       [L("Session lifecycle", "intermediate", 15, "session-management",
          "A session begins at login and should be bound to a strong, random identifier. "
          "Regenerate the session id on privilege change (login) to prevent fixation. "
          "Expire sessions after inactivity and on logout. Store session state server-"
          "side; the cookie should be an opaque reference, as Pwnforge does.",
          exercises=[mcq("To prevent session fixation you should:",
                         ["Reuse the id", "Regenerate the id at login",
                          "Store it in localStorage", "Disable cookies"],
                         "Regenerate the id at login", "session-management",
                         "Regenerating on login defeats fixation.")],
          hints=["The cookie should reference server-side state, not contain it."]),
        L("Protecting the cookie", "intermediate", 10, "session-management",
          "Set `Secure`, `HttpOnly`, and `SameSite` on session cookies. Pair state-"
          "changing requests with anti-CSRF tokens. These measures resist theft and "
          "cross-site abuse.",
          exercises=[short("Token that protects state-changing requests cross-site? (acronym)",
                           "CSRF", "session-management", "Anti-CSRF tokens.")])],
       [mcq("Session ids should be:", ["Sequential", "Guessable", "Strong and random",
            "The username"], "Strong and random", "session-management",
            "Unpredictable ids resist guessing."),
        short("Regenerate the session id at ___.", "login", "session-management",
              "Regenerate on login.")]),

    _c("access-control-course", "Access Control",
       "Authorisation models and enforcing them correctly.",
       "intermediate", ["web-application-security"],
       [L("Authentication vs authorisation", "intermediate", 15, "access-control",
          "Authentication proves *who* you are; authorisation decides *what* you may do. "
          "Broken access control — missing server-side checks, IDs you can tamper with, "
          "trusting the client — is consistently among the most common web risks. Every "
          "sensitive action must be checked server-side against the current user.",
          exercises=[mcq("Authorisation decides:",
                         ["Who you are", "What you may do", "Your IP", "Your browser"],
                         "What you may do", "access-control",
                         "Authorisation governs permitted actions.")],
          hints=["Never trust the client to enforce access."]),
        L("IDOR and the confused deputy", "intermediate", 15, "access-control",
          "Insecure Direct Object Reference (IDOR) lets a user access another's object "
          "by changing an identifier because the server failed to check ownership. The "
          "fix: always verify the current user is authorised for the specific object, "
          "server-side, on every request. Pwnforge enforces per-user ownership on labs "
          "and terminals for exactly this reason.",
          exercises=[short("Accessing another user's record by changing an id is called ___ (acronym).",
                           "IDOR", "access-control", "Insecure Direct Object Reference.")])],
       [mcq("Where must access checks happen?", ["Client only", "Server-side",
            "In the cookie", "In DNS"], "Server-side", "access-control",
            "Authorisation must be enforced server-side."),
        short("Broken ___ control is a top web risk.", "access", "access-control",
              "Broken access control.")],
       cprereqs=["access-control"], lab="web-security-lab"),

    _c("api-security", "API Security",
       "Securing REST and GraphQL interfaces.",
       "hard", ["access-control-course", "authentication-security"],
       [L("API authentication and authorisation", "hard", 20, "api-security",
          "APIs need robust auth: tokens (e.g. OAuth2/JWT) validated on every request, "
          "with authorisation checks per object and per action. Common failures: "
          "accepting unverified tokens, missing object-level checks (the API equivalent "
          "of IDOR), and excessive data exposure where the API returns more than the "
          "client needs.",
          exercises=[mcq("'Broken object level authorization' is essentially:",
                         ["A DNS bug", "IDOR for APIs", "A TLS bug", "A caching bug"],
                         "IDOR for APIs", "api-security",
                         "BOLA is object-level access control failure in APIs.")],
          hints=["Check every object on every request."]),
        L("Rate limiting and schema discipline", "hard", 15, "api-security",
          "APIs should enforce rate limits, validate request schemas strictly, and avoid "
          "returning internal fields. For GraphQL, limit query depth/complexity to "
          "prevent resource exhaustion. Document and version the API clearly.",
          exercises=[short("Control that prevents API abuse by volume?", "rate limiting",
                           "api-security", "Rate limiting caps request volume.")])],
       [mcq("Excessive data exposure means the API:",
            ["Is too slow", "Returns more than the client needs", "Uses UDP",
             "Lacks TLS"], "Returns more than the client needs", "api-security",
            "Return only what is needed."),
        short("API equivalent of IDOR (acronym)?", "BOLA", "api-security",
              "Broken Object Level Authorization.")]),

    _c("file-upload-security", "File Upload Security",
       "Handling uploaded content without creating execution or traversal risks.",
       "hard", ["web-application-security"],
       [L("Why uploads are dangerous", "hard", 20, "file-upload-security",
          "Uploads combine several risks: a file that can be executed by the server, a "
          "path that escapes the intended directory, and content that is actually a "
          "different type than claimed. Defences: validate type by content not extension, "
          "store outside the web root, generate server-side filenames, and never execute "
          "uploaded content.",
          exercises=[mcq("Safest place to store uploads:",
                         ["Inside the web root", "Outside the web root, non-executable",
                          "In /etc", "In the DB schema"],
                         "Outside the web root, non-executable", "file-upload-security",
                         "Keep uploads out of executable web paths.")],
          hints=["Trust content inspection, not the file extension."]),
        L("Filenames and traversal", "hard", 15, "path-traversal",
          "User-supplied filenames can contain `../` sequences aiming to write outside "
          "the target directory. Generate your own safe names and resolve/validate the "
          "final path against the intended base directory before writing.",
          exercises=[short("The sequence used to escape directories is ___ (two dots slash).",
                           "../", "path-traversal", "`../` climbs directories.")])],
       [mcq("Validate file type by:", ["Extension", "Content/magic bytes",
            "Filename length", "Upload speed"], "Content/magic bytes",
            "file-upload-security", "Inspect content, not the extension."),
        short("Store uploads ___ the web root (outside/inside)?", "outside",
              "file-upload-security", "Outside the web root.")],
       cprereqs=["input-validation"]),

    _c("ssrf-course", "Server-Side Request Forgery",
       "How SSRF arises and how to constrain outbound requests.",
       "hard", ["api-security"],
       [L("Understanding SSRF", "hard", 20, "ssrf",
          "SSRF occurs when an application fetches a URL supplied or influenced by a "
          "user, letting it reach internal services the user could not reach directly "
          "(metadata endpoints, internal APIs). Defences: allowlist destinations, resolve "
          "and validate the target address, block internal ranges, and avoid passing raw "
          "user URLs to request libraries.",
          exercises=[mcq("A strong SSRF control is:",
                         ["Blocklisting a few words", "Allowlisting permitted destinations",
                          "Bigger timeouts", "Disabling TLS"],
                         "Allowlisting permitted destinations", "ssrf",
                         "Allowlists constrain where the server may connect.")],
          hints=["Validate the resolved IP, not just the hostname string."])],
       [mcq("SSRF lets an attacker make the server reach:",
            ["Only public sites", "Internal services it should not", "Its own logs",
             "The user's browser"], "Internal services it should not", "ssrf",
            "SSRF pivots to internal resources."),
        short("Preferred SSRF control: ___-list destinations.", "allow", "ssrf",
              "Allowlisting is preferred.")]),

    _c("path-traversal-course", "Path Traversal",
       "Preventing directory traversal when serving or reading files.",
       "intermediate", ["web-application-security"],
       [L("Traversal and canonicalisation", "intermediate", 15, "path-traversal",
          "When a path is built from user input, sequences like `../` can escape the "
          "intended directory and read sensitive files. The fix is to canonicalise the "
          "resolved path and confirm it still lives under the intended base directory "
          "before any file operation — never to blocklist characters.",
          exercises=[mcq("Best traversal defence:",
                         ["Blocklist ../", "Canonicalise and confirm path is under base dir",
                          "URL-encode once", "Lowercase the path"],
                         "Canonicalise and confirm path is under base dir",
                         "path-traversal", "Resolve then verify containment.")],
          hints=["Resolve the final absolute path, then check its prefix."])],
       [short("Sequence used to climb directories?", "../", "path-traversal",
              "`../` climbs directories."),
        mcq("Correct defence:", ["Blocklist", "Canonicalise + containment check",
            "Hide errors", "Rate limit"], "Canonicalise + containment check",
            "path-traversal", "Verify the resolved path stays in bounds.")]),

    _c("advanced-web-security", "Advanced Web Application Security",
       "Chaining weaknesses, assessment methodology and a capstone web lab.",
       "advanced", ["ssrf-course", "cross-site-scripting", "access-control-course"],
       [L("Thinking in attack paths", "advanced", 25, "advanced-web",
          "Real assessments rarely rely on one bug. An analyst maps how lower-severity "
          "issues chain: an information leak reveals an endpoint, weak access control "
          "exposes an object, and a parsing flaw completes the path. The defensive "
          "lesson is that layered, independent controls break chains — and that review "
          "must consider combinations, not isolated findings.",
          exercises=[mcq("Why do chained low-severity issues matter?",
                         ["They don't", "Combined they can enable serious impact",
                          "They speed the site", "They reduce logs"],
                         "Combined they can enable serious impact", "advanced-web",
                         "Chains turn minor issues into major impact.")],
          hints=["Look for how findings enable one another."]),
        L("Structured assessment and reporting", "advanced", 20, "security-reporting",
          "A professional assessment follows a methodology: scope, enumerate, verify, "
          "assess impact, and report with clear reproduction steps and remediation. The "
          "capstone lab asks you to assess a multi-page application, confirm issues "
          "safely, and write up findings with prioritised fixes.",
          exercises=[short("A finding report needs reproduction steps and ___.",
                           "remediation", "security-reporting", "Report fixes too.")])],
       [mcq("Advanced assessment considers:", ["Single bugs only", "Combinations/chains",
            "Only XSS", "Only SQLi"], "Combinations/chains", "advanced-web",
            "Consider how issues combine."),
        short("Reports prioritise findings by ___ (and likelihood).", "impact",
              "security-reporting", "Impact drives prioritisation.")],
       cprereqs=["advanced-web", "access-control"], lab="web-security-lab"),
]
