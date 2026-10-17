"""Official MemoryArena adapter for `agent-memory` (https://github.com/dorianherle/agent_memory).

Implements the `memory/memory_systems/` interface (`add_chunk`, `wrap_user_prompt`)
with deterministic `<= 1,200`-char state packets (`render_packet`), consecutive
compression, and single-call symbol-aware full lookup (`memory_find(query, full=True)`).

Install:
    pip install git+https://github.com/dorianherle/agent_memory.git
"""

from __future__ import annotations

from pathlib import Path
import re
import shutil
import tempfile
from typing import Optional

try:
    from agent_memory import Memory
    from agent_memory.tools import call_tool
except ImportError:  # pragma: no cover - optional until agent_memory backend is selected
    Memory = None  # type: ignore[assignment]
    call_tool = None  # type: ignore[assignment]


class AgentMemorySystem:
    """Consecutive-compression + single-call `full=True` FTS5 memory system for MemoryArena."""

    def __init__(
        self,
        user_id: Optional[str] = None,
        mode: str = "single_call_full",
        workspace_root: Optional[str | Path] = None,
    ):
        if Memory is None:
            raise ImportError(
                "agent-memory is required for AgentMemorySystem. "
                "Install via: pip install git+https://github.com/dorianherle/agent_memory.git"
            )
        self.user_id = user_id or "default"
        self.mode = mode
        self._owns_tempdir = workspace_root is None
        if workspace_root is None:
            self._root = Path(tempfile.mkdtemp(prefix=f"memoryarena_{self.user_id}_"))
        else:
            self._root = Path(workspace_root)
            self._root.mkdir(parents=True, exist_ok=True)
        self.mem = Memory(self._root)
        self._step_count = 0
        self._saved_backgrounds: set[str] = set()
        self._step_summaries: list[str] = []
        self._prev_summary_id: Optional[str] = None

    def _ingest_prompt_background(self, prompt: str) -> str:
        """Extract and persist any non-empty `### BACKGROUND:` section from `wrap_user_prompt`."""
        bg_match = re.search(
            r"###\s*BACKGROUND:\s*(.*?)(?=###\s*PROBLEM:|\Z)",
            prompt,
            flags=re.DOTALL | re.IGNORECASE,
        )
        prob_match = re.search(
            r"###\s*PROBLEM:\s*(.*)",
            prompt,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if bg_match:
            bg_text = bg_match.group(1).strip()
            if (
                bg_text
                and bg_text.lower() != "no information provided."
                and bg_text not in self._saved_backgrounds
            ):
                self._saved_backgrounds.add(bg_text)
                self.mem.save(
                    f"Foundational Background Setup:\n{bg_text}",
                    {"goal": True, "step": self._step_count},
                    agent="memoryarena_agent",
                )
        return prob_match.group(1).strip() if prob_match else prompt.strip()

    @staticmethod
    def _extract_key_math(text: str) -> str:
        inline = re.findall(r"\$([^$]{3,80})\$", text)
        commands = re.findall(r"\\[a-zA-Z]+(?:\{[^{}]{1,25}\})+", text)
        symbols = re.findall(r"\b[a-zA-Z]_[a-zA-Z0-9]+\b", text)
        seen: set[str] = set()
        exprs: list[str] = []
        for tok in inline + commands + symbols:
            norm = tok.strip()
            if len(norm) >= 3 and norm not in seen:
                seen.add(norm)
                exprs.append(f"${norm}$")
        return ", ".join(exprs[:8])

    def add_chunk(self, chunk: str) -> str:
        """Store completed session output and update the consecutive derivation summary."""
        text = (chunk or "").strip()
        if not text or text.startswith("Initial result: Empty"):
            return "ignored_empty"

        # Strip verbose tool trace dumps from MathAgent.build_memory_entry if present
        clean_text = re.split(r"\n##\s*Tool Calls Info:", text, maxsplit=1)[0].strip()

        self._step_count += 1
        note_id = self.mem.save(
            f"Subtask {self._step_count} Solved Result:\n{clean_text}",
            {"step": self._step_count},
            agent="memoryarena_agent",
        )
        key_math = self._extract_key_math(clean_text)
        sol_match = re.search(r"##\s*solution:\s*(.*)", clean_text, flags=re.DOTALL | re.IGNORECASE)
        sol_body = sol_match.group(1).strip() if sol_match else clean_text
        self._step_summaries.append(
            f"Step {self._step_count} key equations: {key_math}\n"
            f"Conclusion: {sol_body[-450:]}"
        )

        if self._step_count >= 2:
            if self._prev_summary_id:
                self.mem.delete(self._prev_summary_id)
            self._prev_summary_id = self.mem.save(
                f"Consecutive Formal State (Steps 1..{self._step_count}):\n"
                + "\n\n".join(self._step_summaries),
                summary=True,
                agent="memoryarena_agent",
            )
        return note_id

    def wrap_user_prompt(self, prompt: str) -> str:
        """Retrieve `MEMORY STATE` + single-call `memory_find(query=..., full=True)`."""
        question = self._ingest_prompt_background(prompt)
        if self._step_count == 0 and len(self._saved_backgrounds) <= 1:
            # First session already has `### BACKGROUND:` inline in `prompt`
            return f"<memory_context>\nNone\n</memory_context>\nUser: {prompt}"

        packet = self.mem.render_packet(question)
        if self.mode == "passive_state":
            mem_ctx = packet
        else:
            found = call_tool(
                self.mem,
                "memory",
                {"action": "find", "query": question, "full": True},
            )
            # Ensure foundational goal=True setup note is always present on deep (k>5) chains
            state_items = self.mem.state()
            goal_items = [
                it for it in state_items if it.payload.get("goal") is True
            ]
            extra_goal = ""
            if goal_items and f"[{goal_items[0].id}]" not in found:
                extra_goal = f"\n[{goal_items[0].id}] {goal_items[0].message}"
            mem_ctx = (
                f"{packet}\n\n"
                f"## Retrieved Memory Notes (memory_find query full=True)\n{found}{extra_goal}"
            )

        return f"<memory_context>\n{mem_ctx}\n</memory_context>\nUser: {prompt}"

    def close(self) -> None:
        if self._owns_tempdir and self._root.exists():
            shutil.rmtree(self._root, ignore_errors=True)
