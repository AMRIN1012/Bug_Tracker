"""
AI Bug Assistant Engine
=======================
Provides intelligent heuristics for auto-triage, severity prediction,
duplicate detection, root cause suggestion, developer recommendation,
and fix templates. Optionally uses Gemini AI if GEMINI_API_KEY env var is set.
"""
import os
import re
from difflib import SequenceMatcher


# --- Keyword-based heuristic maps ---

SEVERITY_KEYWORDS = {
    'Blocker': ['crash', 'fatal', 'data loss', 'database corruption', 'system down', 'cannot login',
                'server error', '500', 'production down', 'sql injection', 'security breach',
                'payment failed', 'data breach', 'out of memory', 'infinite loop'],
    'Critical': ['critical', 'broken', 'major issue', 'authentication fail', 'incorrect data',
                 'data mismatch', 'privilege escalation', 'xss', 'injection', 'token leak',
                 'performance degradation', 'timeout', 'api failure', 'null pointer'],
    'Major': ['cannot', 'not working', 'incorrect', 'wrong', 'unexpected', 'error', 'exception',
              'fail', 'broken link', 'redirect issue', 'missing validation', 'upload fail'],
    'Minor': ['ui', 'alignment', 'typo', 'spacing', 'color', 'label', 'tooltip', 'icon', 'style',
              'cosmetic', 'minor', 'spelling', 'font', 'margin', 'padding'],
}

PRIORITY_KEYWORDS = {
    'Critical': ['blocker', 'critical', 'production', 'data loss', 'security', 'crash', 'payment',
                 'authentication', 'login', 'cannot access', 'server down'],
    'High': ['broken', 'urgent', 'major', 'regression', 'milestone', 'sprint', 'deadline'],
    'Medium': ['moderate', 'medium', 'should fix', 'important'],
    'Low': ['enhancement', 'cosmetic', 'minor', 'nice to have', 'suggestion', 'documentation'],
}

MODULE_KEYWORDS = {
    'Authentication': ['login', 'logout', 'register', 'password', 'oauth', 'token', 'session', 'auth'],
    'API Layer': ['api', 'endpoint', 'request', 'response', 'rest', 'graphql', 'json', 'http', '404', '500'],
    'Database': ['database', 'db', 'sql', 'query', 'migration', 'schema', 'table', 'index'],
    'UI/Frontend': ['ui', 'css', 'style', 'layout', 'responsive', 'button', 'form', 'modal', 'page'],
    'Security': ['security', 'xss', 'injection', 'privilege', 'permission', 'access control', 'vulnerability'],
    'Performance': ['slow', 'performance', 'timeout', 'memory', 'cpu', 'lag', 'latency', 'bottleneck'],
    'Notifications': ['notification', 'email', 'sms', 'alert', 'push', 'webhook'],
    'Search': ['search', 'filter', 'query', 'pagination', 'sort'],
    'File Management': ['upload', 'download', 'file', 'attachment', 'image', 's3', 'storage'],
    'Reports': ['report', 'export', 'pdf', 'csv', 'excel', 'analytics', 'dashboard'],
}

ROOT_CAUSE_TEMPLATES = {
    'Authentication': [
        "Token expiry handling may be missing or incorrect.",
        "Session cookie not being set with correct domain/path.",
        "OAuth redirect URI mismatch between client and provider.",
    ],
    'API Layer': [
        "Missing error handling for non-200 HTTP responses.",
        "Incorrect Content-Type header in request/response.",
        "Rate limiting or API quota exceeded.",
        "Serializer validation error — check required fields.",
    ],
    'Database': [
        "Missing database index causing slow query performance.",
        "Incorrect foreign key relationship or null constraint violation.",
        "Migration not applied — try running 'python manage.py migrate'.",
    ],
    'UI/Frontend': [
        "CSS specificity conflict overriding intended styles.",
        "JavaScript event listener firing on incorrect element.",
        "Responsive breakpoint not handled for this screen size.",
    ],
    'Security': [
        "User input not being sanitized before database query (SQL injection risk).",
        "Missing CSRF token validation on this endpoint.",
        "Incorrect permission check — user can access resource they shouldn't.",
    ],
    'Performance': [
        "N+1 database query issue — use select_related() or prefetch_related().",
        "Heavy synchronous operation blocking the request thread — offload to Celery.",
        "Missing caching layer — consider using Redis or Memcached.",
    ],
}

FIX_TEMPLATES = {
    'Authentication': [
        "Verify token refresh logic and add token expiry handling with try/except.",
        "Clear browser cookies and test with a fresh session.",
        "Double-check OAuth redirect URI in both provider settings and application config.",
    ],
    'API Layer': [
        "Add try/except around API call with proper error response codes.",
        "Use Postman or curl to manually reproduce the API request and trace the error.",
        "Review serializer code and ensure all required fields are validated.",
    ],
    'Database': [
        "Run 'EXPLAIN ANALYZE' on the slow query and add composite indexes.",
        "Check migration history: python manage.py showmigrations.",
        "Verify null=True/blank=True settings match database constraints.",
    ],
    'UI/Frontend': [
        "Open browser DevTools → Elements → inspect computed styles for conflicts.",
        "Test across Chrome, Firefox, and Safari to identify browser-specific issues.",
        "Add media query overrides for the affected screen size breakpoint.",
    ],
    'Security': [
        "Use Django ORM with parameterized queries instead of raw SQL strings.",
        "Add @login_required and permission_required decorators to the view.",
        "Verify CSRF middleware is active and token is present in all POST forms.",
    ],
    'Performance': [
        "Profile view with Django Debug Toolbar to count SQL queries.",
        "Add select_related() to avoid N+1 queries in list views.",
        "Implement caching with Django's cache framework for expensive computations.",
    ],
}


def _normalize(text):
    """Lowercase and strip text for keyword matching."""
    return (text or '').lower().strip()


def _keyword_match(text, keyword_map):
    """Returns the category with the most keyword hits."""
    text = _normalize(text)
    scores = {cat: 0 for cat in keyword_map}
    for cat, keywords in keyword_map.items():
        for kw in keywords:
            if kw in text:
                scores[cat] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None


def predict_severity(title, description):
    """Predict bug severity from title + description using keyword heuristics."""
    combined = f"{title} {description}"
    result = _keyword_match(combined, SEVERITY_KEYWORDS)
    return result or 'Major'


def predict_priority(title, description, environment=''):
    """Predict bug priority."""
    combined = f"{title} {description} {environment}"
    result = _keyword_match(combined, PRIORITY_KEYWORDS)
    return result or 'Medium'


def detect_module(title, description):
    """Detect the likely affected module based on keywords."""
    combined = f"{title} {description}"
    result = _keyword_match(combined, MODULE_KEYWORDS)
    return result or 'General'


def suggest_root_cause(title, description, bug_type=''):
    """Return a list of probable root causes."""
    module = detect_module(title, description)
    causes = ROOT_CAUSE_TEMPLATES.get(module, [
        "Review recent code changes in the affected module.",
        "Check for environment-specific configuration differences.",
        "Look for recent dependency or library version changes.",
    ])
    return causes[:2]  # Return top 2


def suggest_fix(title, description, bug_type=''):
    """Return a list of recommended fix steps."""
    module = detect_module(title, description)
    fixes = FIX_TEMPLATES.get(module, [
        "Reproduce the issue locally using the provided steps.",
        "Review the relevant code path and add proper error handling.",
        "Write a unit test that covers this scenario before fixing.",
    ])
    return fixes[:2]


def generate_title(raw_input):
    """Generate a clean, professional bug title from raw input."""
    title = raw_input.strip()
    if len(title) > 100:
        # Truncate and clean
        title = title[:97] + '...'
    # Capitalize first letter
    return title[0].upper() + title[1:] if title else title


def generate_description(title, steps='', expected='', actual='', environment=''):
    """Generate a structured professional description template."""
    parts = []
    if title:
        parts.append(f"**Issue:** {title}\n")
    if environment:
        parts.append(f"**Environment:** {environment}\n")
    if steps:
        parts.append(f"**Steps to Reproduce:**\n{steps}\n")
    if expected:
        parts.append(f"**Expected Result:**\n{expected}\n")
    if actual:
        parts.append(f"**Actual Result:**\n{actual}\n")
    if not parts:
        parts.append("Please provide a detailed description of the issue.")
    return '\n'.join(parts)


def detect_duplicate(new_title, new_description, existing_bugs):
    """
    Compare a new bug against existing ones and return potential duplicates.
    Returns a list of (bug, similarity_score) tuples above a threshold.
    """
    combined_new = _normalize(f"{new_title} {new_description}")
    duplicates = []
    for bug in existing_bugs:
        combined_existing = _normalize(f"{bug.title} {bug.description}")
        ratio = SequenceMatcher(None, combined_new, combined_existing).ratio()
        if ratio > 0.55:
            duplicates.append({'bug': bug, 'score': round(ratio * 100, 1)})
    duplicates.sort(key=lambda x: x['score'], reverse=True)
    return duplicates[:5]


def recommend_developer(title, description, developers):
    """
    Recommend a developer based on keyword matching against module expertise
    and their current open bug workload (lighter workload = better candidate).
    Returns a list of recommended developers with reasoning.
    """
    module = detect_module(title, description)
    recommendations = []
    for dev in developers:
        open_count = dev.assigned_bugs.exclude(
            status__in=['Passed', 'Closed', 'Rejected']
        ).count()
        # Score: lower workload = higher score, bonus for module keyword match
        workload_score = max(0, 10 - open_count)
        expertise_keywords = MODULE_KEYWORDS.get(module, [])
        activity_text = _normalize(
            ' '.join([log.details or '' for log in dev.activity_logs.all()[:30]])
        )
        expertise_score = sum(1 for kw in expertise_keywords if kw in activity_text)
        total_score = workload_score + expertise_score
        recommendations.append({
            'user': dev,
            'open_bugs': open_count,
            'module': module,
            'score': total_score,
        })
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    return recommendations[:3]


def estimate_fix_time(severity, bug_type):
    """Estimate fix time in hours based on severity and bug type."""
    time_map = {
        ('Blocker', 'Security Bug'): (4, 16),
        ('Blocker', 'Database Bug'): (4, 12),
        ('Blocker', 'API Bug'): (3, 10),
        ('Critical', 'Security Bug'): (3, 8),
        ('Critical', 'Functional Bug'): (2, 8),
        ('Major', 'Functional Bug'): (1, 4),
        ('Major', 'Performance Bug'): (2, 8),
        ('Minor', 'UI Bug'): (0.5, 2),
        ('Minor', 'Functional Bug'): (0.5, 3),
    }
    low, high = time_map.get((severity, bug_type), (1, 4))
    return f"{low}–{high} hours"


def generate_reproduction_checklist(steps_to_reproduce, environment=''):
    """Generate a checklist of steps needed to reproduce the bug."""
    checklist = []
    if environment:
        checklist.append(f"☐ Set up {environment} environment")
    if steps_to_reproduce:
        lines = [l.strip() for l in steps_to_reproduce.split('\n') if l.strip()]
        for i, line in enumerate(lines[:8], 1):
            if not line.startswith('☐'):
                checklist.append(f"☐ {line}")
    if not checklist:
        checklist = [
            "☐ Set up a clean local/staging environment",
            "☐ Authenticate with affected user role",
            "☐ Navigate to the affected section",
            "☐ Observe and document the error output",
        ]
    return checklist


def full_ai_triage(title, description, bug_type='Functional Bug', environment='Development',
                   steps='', expected='', actual='', existing_bugs=None, developers=None):
    """
    Run a full AI triage on a bug report and return structured recommendations.
    """
    result = {
        'predicted_severity': predict_severity(title, description),
        'predicted_priority': predict_priority(title, description, environment),
        'detected_module': detect_module(title, description),
        'root_causes': suggest_root_cause(title, description, bug_type),
        'fix_suggestions': suggest_fix(title, description, bug_type),
        'estimated_fix_time': estimate_fix_time(
            predict_severity(title, description), bug_type
        ),
        'reproduction_checklist': generate_reproduction_checklist(steps, environment),
        'duplicates': [],
        'recommended_developers': [],
    }

    if existing_bugs:
        result['duplicates'] = detect_duplicate(title, description, existing_bugs)

    if developers:
        result['recommended_developers'] = recommend_developer(title, description, developers)

    # Optional: Call Gemini API if key is configured
    api_key = os.environ.get('GEMINI_API_KEY')
    if api_key:
        try:
            result['ai_summary'] = _call_gemini(api_key, title, description)
        except Exception:
            result['ai_summary'] = None

    return result


def _call_gemini(api_key, title, description):
    """Optional: Call Gemini API for enhanced summarization."""
    import urllib.request, json
    prompt = (
        f"Analyze this bug report and provide a 2-sentence professional summary:\n\n"
        f"Title: {title}\nDescription: {description}"
    )
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = json.loads(resp.read())
        return data['candidates'][0]['content']['parts'][0]['text']
