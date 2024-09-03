import json
import logging
from state import ResearchState, Section, Brief
from llm import get_llm
from prompts import get_router_prompt, get_greeter_prompt, get_planner_prompt, get_researcher_prompt, get_writer_prompt, ResearchTopicRouter
from tools import search
logger = logging.getLogger(__name__)


class ResearchAgent:
    def __init__(self) -> None:
        self._router_llm = get_llm(temperature=0, num_predict=300).with_structured_output(ResearchTopicRouter)
        self._greeter_llm = get_llm(temperature=0.7, num_predict=128)
        self._planner_llm = get_llm(temperature=0, num_predict=2048)
        self._researcher_llm = get_llm(temperature=0.2, num_predict=2048)
        self._writer_llm = get_llm(temperature=0.3, num_predict=8096)


    def router_node(self, state: ResearchState) -> dict:
        user_message = state["user_message"]
        logger.info("Classifying input: '%s'", user_message)

        result: ResearchTopicRouter = self._router_llm.invoke(get_router_prompt(user_message))
        input_type = "topic" if result.is_research_topic else "greeting"

        logger.info("Classified as: '%s' (confidence: %.2f) — %s", input_type, result.confidence_score, result.reasoning)
        return {
            "input_type": input_type,
            "topic": user_message if input_type == "topic" else "",
        }

    def greeter_node(self, state: ResearchState) -> dict:
        logger.info("Generating greeting response")
        response = self._greeter_llm.invoke(get_greeter_prompt(state["user_message"]))
        return {"input_type": "greeting", "output": response.content.strip(), "topic": ""}

    def planner_node(self, state: ResearchState) -> dict:
        topic = state["topic"]
        logger.info("Breaking down topic: '%s'", topic)

        response = self._planner_llm.invoke(get_planner_prompt(topic))
        sections = self._parse_sections(response.content, topic)

        logger.info("Created %d sections: %s", len(sections), [s["title"] for s in sections])
        return {"sections": sections}

    def researcher_node(self, state: dict) -> dict:
        section: Section = state["section"]
        logger.info("Starting section %d: '%s'", section["id"], section["title"])

        try:
            search_text, sources = self._run_search(section)
            findings = self._summarise(section, search_text)
            logger.info("Done section %d: '%s' (%d sources)", section["id"], section["title"], len(sources))
        except Exception as e:
            logger.warning("Section %d '%s' failed — empty brief. Error: %s", section["id"], section["title"], e)
            findings = f"Research unavailable for this section (search failed: {e})"
            sources = []

        return {"briefs": [Brief(
            section_id=section["id"],
            section_title=section["title"],
            findings=findings,
            sources=sources,
        )]}

    def writer_node(self, state: ResearchState) -> dict:
        topic = state["topic"]
        briefs = sorted(state["briefs"], key=lambda b: b["section_id"])
        logger.info("Synthesising %d briefs into final report...", len(briefs))

        prompt = get_writer_prompt(topic=topic, briefs_text=self._format_briefs(briefs))
        response = self._writer_llm.invoke(prompt)
        report = response.content.strip()

        return {"report": report, "output": report}

    def _parse_sections(self, raw_content: str, topic: str) -> list[Section]:
        content = raw_content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Planner returned invalid JSON for topic '{topic}'.\n"
                f"Parse error: {e}\nRaw response:\n{raw_content}"
            )

        raw_sections = data.get("sections", [])
        if not raw_sections:
            raise ValueError(f"Planner returned no sections for topic '{topic}'.\nResponse was: {data}")

        sections: list[Section] = []
        for i, s in enumerate(raw_sections):
            if "title" not in s or "queries" not in s:
                raise ValueError(f"Section {i} missing 'title' or 'queries'. Got: {s}")
            sections.append(Section(
                id=s.get("id", i + 1),
                title=s["title"],
                description=s.get("description", ""),
                queries=s["queries"],
            ))
        return sections

    def _run_search(self, section: Section) -> tuple[str, list[str]]:
        try:
            return search(section["queries"])
        except RuntimeError as e:
            raise RuntimeError(f"Search failed for section '{section['title']}' (id={section['id']}):\n{e}")

    def _summarise(self, section: Section, search_text: str) -> str:
        prompt = get_researcher_prompt(
            section_title=section["title"],
            section_description=section["description"],
            search_results=search_text,
        )
        return self._researcher_llm.invoke(prompt).content.strip()

    def _format_briefs(self, briefs: list[Brief]) -> str:
        parts = []
        for brief in briefs:
            sources_block = ""
            if brief["sources"]:
                sources_block = "\nSources:\n" + "\n".join(f"  - {u}" for u in brief["sources"])
            parts.append(
                f"=== Section {brief['section_id']}: {brief['section_title']} ===\n"
                f"{brief['findings']}{sources_block}"
            )
        return "\n\n".join(parts)
