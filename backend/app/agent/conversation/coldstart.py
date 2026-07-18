"""Cold-start clarification: per-category question frames plus
preference-aware follow-ups, one question per turn, at most three per cycle,
never re-asking an answered or already-asked question."""

from dataclasses import dataclass

from backend.app.agent.contracts import AgentState, GenericNeed
from backend.app.agent.conversation.scenario_data import SCENARIOS

MAX_QUESTIONS_PER_CYCLE = 3


@dataclass(frozen=True, slots=True)
class Question:
    key: str
    ask: str


def _question_answered(key: str, need: GenericNeed) -> bool:
    if key == "budget":
        return need.budget_max is not None or need.budget_min is not None
    if key in ("purpose",):
        return need.usage_purpose is not None
    if key in need.attribute_constraints:
        return True
    return key in {p.lower() for p in need.priorities}


def _script_for(need: GenericNeed) -> list[Question]:
    scenario = SCENARIOS.get(need.category_code or "")
    if scenario is None:
        return []
    questions = [Question(q["key"], q["ask"]) for q in scenario["questions"]]
    purpose = (need.usage_purpose or "").lower()
    if purpose:
        for trigger, followups in scenario.get("purpose_followups", {}).items():
            if trigger in purpose:
                questions.extend(Question(q["key"], q["ask"]) for q in followups)
    return questions


def performance_attribute(category_code: str | None) -> str | None:
    scenario = SCENARIOS.get(category_code or "")
    return scenario.get("performance_attribute") if scenario else None


def question_example(category_code: str | None, key: str | None) -> str | None:
    """Concrete example for an abstract cold-start question, used when the
    customer asks what the question means and in the missing-info hint."""
    scenario = SCENARIOS.get(category_code or "")
    if not scenario or key is None:
        return None
    for question in scenario.get("questions", []):
        if question["key"] == key:
            return question.get("example")
    for followups in scenario.get("purpose_followups", {}).values():
        for question in followups:
            if question["key"] == key:
                return question.get("example")
    return None


def purpose_example(category_code: str | None) -> str | None:
    scenario = SCENARIOS.get(category_code or "")
    return scenario.get("purpose_example") if scenario else None


def opening_questions(state: AgentState, *, limit: int = 3) -> list[Question]:
    """First contact with a category: bundle the top 2-3 unanswered questions
    into ONE message (Cường's cold-start direction). The bundle counts as a
    single clarification turn; all bundled keys are marked asked and the
    pending key is the first one."""
    category = state.need.category_code
    if category is None:
        return []
    asked = state.asked_for(category)
    questions: list[Question] = []
    for question in _script_for(state.need):
        if len(questions) >= limit:
            break
        if question.key in asked or _question_answered(question.key, state.need):
            continue
        asked.append(question.key)
        questions.append(question)
    if questions:
        state.clarification_count[category] = (
            state.clarification_count.get(category, 0) + 1
        )
        state.pending_question_key = questions[0].key
        state.pending_question_text = questions[0].ask
    return questions


def render_opening(questions: list[Question], category_name: str) -> str:
    if len(questions) == 1:
        return questions[0].ask
    marks = ["①", "②", "③"]
    lines = [
        f"Dạ để tư vấn {category_name} chuẩn nhất, anh/chị cho em xin vài "
        "thông tin ạ:",
    ]
    for index, question in enumerate(questions):
        lines.append(f"{marks[index]} {question.ask}")
    return "\n".join(lines)


def next_question(state: AgentState) -> Question | None:
    """Pick the highest-importance unanswered, un-asked question for the
    current category, or None when the cycle budget is spent / nothing is
    missing."""
    need = state.need
    category = need.category_code
    if category is None:
        return None
    if state.clarification_count.get(category, 0) >= MAX_QUESTIONS_PER_CYCLE:
        return None
    asked = state.asked_for(category)
    for question in _script_for(need):
        if question.key in asked:
            continue
        if _question_answered(question.key, need):
            continue
        return question
    return None


def record_asked(state: AgentState, question: Question) -> None:
    category = state.need.category_code or ""
    state.asked_for(category).append(question.key)
    state.clarification_count[category] = state.clarification_count.get(category, 0) + 1


def has_material_minimum(need: GenericNeed) -> bool:
    """Enough to search usefully: a category plus either a budget or at least
    one narrowing fact (purpose, constraint, brand, or priority)."""
    if need.category_code is None:
        return False
    narrowing = (
        need.budget_max is not None
        or need.budget_min is not None
        or need.usage_purpose is not None
        or bool(need.attribute_constraints)
        or bool(need.brand_prefs)
        or bool(need.priorities)
    )
    return narrowing
