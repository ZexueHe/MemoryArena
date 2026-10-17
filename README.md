# MemoryArena

Minimal, modular framework for connecting agents, environments, and memory.

Implementation for **MemoryArena: Benchmarking Agent Memory in Interdependent Multi-Session Agentic Tasks** (https://arxiv.org/abs/2602.16313). 

*This code is preview version. We are still actively maintaining and improving this codebase.*
## Quick Start 
**[Important]** Check `setup_web_shopping.md`, `setup_travel.md`, `setup_web_search_env.md`, and `setup_formal_reasoning.md`to follow step-by-step structions for each test environment.

## Repository Structure

- `agent/`: task agent implementations.
- `env/`: environment server, client, and environment systems.
- `memory/`: memory client and memory systems including long-context, letta, mirix, mem0, mem0-g, ReasoningBank, BM25, Text-embedding RAG, GraphRAG, MemoRAG, and Agent Memory (`agent_memory`). 

## API Keys
- Make sure you have your `OPENAI_API_KEY`, `OPENAI_BASE_URL`,  `GOOGLE_API_KEY`,  `ANTHROPIC_API_KEY`,  `OPENROUTER_API_KEY`, `OPENROUTER_API_BASE_URL` set ready in either your bashrc file or in configs following each setup `md`.
- For Letta, Mirix, Mem0 (including Mem0-g), make sure you have their memory system api keys ready `LETTA_API_KEY`, `MIRIX_API_KEY`, `MEM0_API_KEY` in your bashrc file. 

## Example Flow

1. Task prompt → memory wraps prompt
2. Agent generates action
3. Env `step()` executes tool or accepts final
4. Observation + reward returned
5. Memory stores action/observation/reward(optional)

## Leaderboard (`formal_reasoning_phys` — 20 Papers, 86 Subtasks)

| Rank | Memory System | Solver Backbone | Success Rate (SR) | Progress Score (PS) | Avg Memory Tokens | Source / Logs |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **1** | **[Agent Memory (`agent_memory`)](https://github.com/dorianherle/agent_memory)** | `gpt-5.6-sol` | **100.0% (`20/20`)** | **100.0% (`86/86`)** | `968.0` | [Logs & Paper](https://github.com/dorianherle/agent_memory/tree/main/benchmarks/memoryarena/official_results/phys/agent_memory_single_call_full) |
| **2** | **[Agent Memory Passive (`agent_memory_passive`, 0 calls)](https://github.com/dorianherle/agent_memory)** | `gpt-5.6-sol` | **75.0% (`15/20`)** | **85.8%** | **`197.3`** | [Logs](https://github.com/dorianherle/agent_memory/tree/main/benchmarks/memoryarena/official_results/phys/agent_memory_passive_state) |
| **3** | **[Agent Memory (`agent_memory`)](https://github.com/dorianherle/agent_memory)** | `gpt-5-mini` (Official) | **50.0% (`10/20`)** | **60.2%** | `1,434.9` | [Logs](https://github.com/dorianherle/agent_memory/tree/main/benchmarks/memoryarena/official_results/phys/agent_memory_single_call_full_gpt5mini) |
| **4** | **[Agent Memory Passive (`agent_memory_passive`, 0 calls)](https://github.com/dorianherle/agent_memory)** | `gpt-5-mini` (Official) | **50.0% (`10/20`)** | **56.9%** | **`198.3`** | [Logs](https://github.com/dorianherle/agent_memory/tree/main/benchmarks/memoryarena/official_results/phys/agent_memory_passive_state_gpt5mini) |
| 5 | Long-Context (`gpt-5.1-mini`) | `gpt-5.1-mini` | 45.0% (`9/20`) | 60.0% | Full Trace | [Paper Table 3](https://arxiv.org/abs/2602.16313) |
| 6 | Letta (MemGPT) | `gpt-5-mini` | 45.0% (`9/20`) | 56.6% | — | [Paper Table 3](https://arxiv.org/abs/2602.16313) |
| 7 | BM25 Chunk RAG | `gpt-5-mini` | 25.0% (`5/20`) | 50.5% | `243.6` | [Logs](https://github.com/dorianherle/agent_memory/tree/main/benchmarks/memoryarena/official_results/phys/bm25_chunk_rag_gpt5mini) |
| 8 | Mem0-style Extracted Facts | `gpt-5-mini` | 15.0% (`3/20`) | 38.9% | `109.3` | [Logs](https://github.com/dorianherle/agent_memory/tree/main/benchmarks/memoryarena/official_results/phys/mem0_style_extracted_facts_gpt5mini) |
| 9 | No Memory | `gpt-5-mini` | 5.0% (`1/20`) | 32.2% | `0.0` | [Logs](https://github.com/dorianherle/agent_memory/tree/main/benchmarks/memoryarena/official_results/phys/no_memory_gpt5mini) |

# Cite Our Paper:
If you are using this repo, please cite our paper at:
```
@article{he2026memoryarena,
  title={MemoryArena: Benchmarking Agent Memory in Interdependent Multi-Session Agentic Tasks},
  author={He, Zexue and Wang, Yu and Zhi, Churan and Hu, Yuanzhe and Chen, Tzu-Ping and Yin, Lang and Chen, Ze and Wu, Tong Arthur and Ouyang, Siru and Wang, Zihan and others},
  journal={arXiv preprint arXiv:2602.16313},
  year={2026}
}
```

