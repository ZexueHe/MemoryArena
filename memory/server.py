import os
from typing import Dict, Callable, NamedTuple

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from memory_systems import (
    LongContextMemorySystem, 
    MirixMemorySystem, 
    Mem0MemorySystem, 
    LettaMemorySystem, 
    RAGMemorySystem, 
    MemoRAGMemorySystem,
    GraphRAGMemorySystem,
    AMemMemorySystem,
    LightMemMemorySystem,
    ReasoningBankMemorySystem,
    ZepMemorySystem,
    AgentMemorySystem,
)


load_dotenv()

# ---------- Request schemas ----------
class InitializeRequest(BaseModel):
    user_id: str
    memory_system_name: str


class AddRequest(BaseModel):
    user_id: str
    chunk: str
    memory_system_name: str


class QueryRequest(BaseModel):
    user_id: str
    question: str
    memory_system_name: str

class ActRequest(BaseModel):
    user_id: str
    prompt: str
    memory_system_name: str

# ---------- Memory/Agent implementations (unified) ----------
MEMORY_FACTORIES: Dict[str, Callable[[], object]] = {
    "mirix": MirixMemorySystem,
    "long_context": LongContextMemorySystem,
    "mem0": Mem0MemorySystem,
    "mem0-g": lambda: Mem0MemorySystem(enable_graph=True),
    "letta": LettaMemorySystem,
    "rag": RAGMemorySystem,
    "memorag": MemoRAGMemorySystem,
    "graphrag": GraphRAGMemorySystem,
    "amem": AMemMemorySystem,
    "lightmem": LightMemMemorySystem,
    "reasoningbank": ReasoningBankMemorySystem, # You must add user_id when initializing ReasoningBankMemorySystem
    "zep": ZepMemorySystem,
    "agent_memory": lambda: AgentMemorySystem(mode="single_call_full"),
    "agent_memory_passive": lambda: AgentMemorySystem(mode="passive_state"),
}


# ---------- FastAPI wiring ----------
app = FastAPI(title="Memory Agent Server")


class MemorySystemEntry(NamedTuple):
    name: str
    system: object


MEMORY_SYSTEMS: Dict[str, MemorySystemEntry] = {}


def _get_memory(user_id: str, memory_system: str):
    entry = MEMORY_SYSTEMS.get(user_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="User not initialized")
    if entry.name != memory_system:
        raise HTTPException(status_code=400, detail="Mismatched memory_system for user")
    return entry.system


@app.post("/memory/initialize")
def initialize(req: InitializeRequest):
    name = req.memory_system_name
    if name in {"bm25", "text-embedding-3-small"}:
        memory_system = RAGMemorySystem(retrieval_method=name)
    # elif name == "graphrag":
    #     if not os.getenv("GRAPHRAG_LOCAL_DIR"):
    #         raise HTTPException(status_code=400, detail="GRAPHRAG_LOCAL_DIR is required to initialize GraphRAG.")
    #     memory_system = GraphRAGMemorySystem(local_dir=os.getenv("GRAPHRAG_LOCAL_DIR"))
    elif name in {"reasoningbank"}:
        memory_system = ReasoningBankMemorySystem(user_id=req.user_id)
    else:
        factory = MEMORY_FACTORIES.get(name)
        if factory is None:
            raise HTTPException(status_code=400, detail=f"Unsupported memory_system: {name}")
        memory_system = factory()
    MEMORY_SYSTEMS[req.user_id] = MemorySystemEntry(name=name, system=memory_system)
    return {"status": "ok", "user_id": req.user_id, "memory_system_name": name}


@app.post("/memory/add")
def add(req: AddRequest):
    memory_system = _get_memory(req.user_id, req.memory_system_name)
    response = memory_system.add_chunk(req.chunk)
    outputs = {"status": "ok", "user_id": req.user_id}
    outputs['response'] = response
    return outputs


@app.post("/memory/wrap_user_prompt")
def wrap_user_prompt(req: QueryRequest):
    memory_system = _get_memory(req.user_id, req.memory_system_name)
    prompt = memory_system.wrap_user_prompt(req.question)
    return {"status": "ok", "user_id": req.user_id, "prompt": prompt}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
