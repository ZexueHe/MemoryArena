# Formal Reasoning (Math and Phys) Environment Setup

## 1. Install Dependencies
We provide full environment in `env/env_systems/formal_reasoning_env/environment.yml` so create the `reasoning` environment by:
```
conda env create -f env/env_systems/formal_reasoning_env/environment.yml
```

## 2. Configures

Each experiment is defined by a JSON config file under `configs/formal_reasoning/`. Pre-built configs are provided for all memory systems.

Example:
```
{
  "task_name": "math", # can change to phys
  "description": "Math reasoning task with memory system",
  
  "agent": {
    "model_name": "gpt-5-mini",
    "temperature": 0.0,
    "max_tokens": 8192,
    "backend": "openai",
    "base_url": "<YOUR_BASE_URL>"
  },
  
  "memory": {
    "session_wise_memory": true,
    "judge_result_in_memory": false,
    "memory_system_name": "bm25",
    "base_url": "http://0.0.0.0:8000", # for memory system
    "timeout": 300
  },
  
  "env": {
    "env_name": "math",
    "base_url": "http://0.0.0.0:8001", # for env server
    "timeout": 300,
    "env_config": {
      "model_name": "gpt-5-mini",
      "temperature": 1.0,
      "max_tokens": 4096,
      "backend": "openai",
      "base_url": "<YOUR_BASE_URL>", # for LLM judge used in env. 
      "max_steps": 10
    }
  },
  
  "task_specific": {
    "max_steps": 10,
    "auto_eval_after_run": true,
    "dataset": {
      "hf_dataset": "ZexueHe/memoryarena", # if you want to test Phys then change this part
      "hf_config": "formal_reasoning_math",  # if you want to test Phys then change this part
      "hf_split": "test"
    }
  },
  
  "output": {
    "json_output_dir": "./results/json/math", # if you want to test Phys then change this part to sth like ./results/json/phys
  }
}
```
Fields you need to set:
| Field | What to set | Note|
|---|---|---|
| `agent.base_url` | Your LLM API base URL |-|
| `agent.model_name` |LLM model used in the task agent (e.g., `gpt-5-mini`, `gemini-3-flash`, `claude-sonnet-4`). | Usually used in long-context memory where this LLM itself is the memory system to test. For other memory system we use `gpt-5-mini` + `<memory system>`. |
| `memory.memory_system_name` | Memory backend to use (e.g., `bm25`, `mirix`, `mem0`) | - |
| `memory.base_url` | where the memory system is hosted at| default port is  `8000`, you can change it but remember to sync the change in `memory/`|
| `env.env_name` | running for `math` for `phys`| math and phys are sharing the same reasoning env.|
| `env.base_url` | where the env api is hosted at| default port is  `8001`, you can change it but remember to sync the change in `env/`|
| `env.env_config.base_url` | Base URL for the judge model API |-|
| `env.env_config.model_name` |  judge model name |-|
| `task_specific.dataset.hf_config` | Dataset config (`formal_reasoning_math` or `formal_reasoning_phys`) | - |
| `output.json_output_dir` | Output directory for this run | Evaluation will read jsons from this dir |



## 3. Run Experiment 

### 3.1 Start Servers

Open two seperate terminals (recommend to use `screen` or `tmux` to make them live long).
```
# Terminal 1: Environment server
python env/env_server.py

# Terminal 2: Memory server (required unless memory_system_name is "none" or "long_context")
python memory/server.py
```

### 3.2 Run and evaluate

```
python run_math.py -c configs/formal_reasoning_configs/<your_config>.json
```

This will:

1. read either math/phys tasks from HuggingFace (cached locally after first download).
2. For each task, the code will generate response for each subtask, run LLM judge (note: we use the session-wise judge result just to evaluate progress score and pass rate at K later, so the judge result won't be added into memory), and run evaluation automatically, with result jsons saved in `config['output']['json_output_dir']` . 

**[optional]** The evaluation code is in `env/env_systems/formal_reasoning_env/eval.py`. So you can also run evaluation in a post-hoc way by
```
# suppose you already run formal reasoning with your json config

python env/env_systems/formal_reasoning_env/eval.py configs/formal_reasoning_configs/<your_config>.json
```

The evaluation results will be saved into `all_results.json` under `config['output']['json_output_dir']/<memory_system_name>`.

Example `all_results.json`
```
{
    "overall_average_passrate": ...,
    "avg_progress_score": ...,
    "average_memory_length": ...,
    "average_session_time": ..,
    "average_data_time": ...,
    "memory_length": ...,
    "min_k": ...,
    "passrate_at_k (not guaranteed monotonic decreasing)": [ ..., ..., ... ],
    "cummulative_passrate_at_k (not guaranteed monotonic decreasing)": [..., ..., ...  ],
    "passrate_at_min_k": [..., ..., ... ],
    "cummulative_passrate_at_min_k": [..., ..., ...] 
}
```

Note: `passrate_at_k` and `cummulative_passrate_at_k` is average over all examples (so even for `cummulative_passrate_at_k` it is not guaranteed to have a monotonic trend), `passrate_at_min_k` and `cummulative_passrate_at_min_k` is average over all examples but stop at minimal length (`min_k`) in all examples (so every example contributes to the calculation). Example:

```
task1: sub1, sub2, sub3, sub4, sub5
task2: sub1, sub2, sub3, sub4, sub5, sub6
task3: sub1, sub2, sub3, sub4, sub5, sub6, sub7
```
- `passrate_at_k` and `cummulative_passrate_at_k`: until k=7;
- `passrate_at_min_k` and `cummulative_passrate_at_min_k`: only until k=5


## 4. Supported Configs

**Available configs** (`configs/formal_reasoning/`):


|Task| Config | Memory System | Model |
|--------|--------|--------------|-------|
| Math   | `math_longcontext_gpt-5-mini.json`| long context | gpt-5-mini
| Math   | `math_longcontext_gemini3.json`| long context | gemini-3-flash-preview
| Math   | `math_longcontext_gemini3.json`| long context | gemini-3-flash-preview
| Math   | `math_longcontext_sonnet4.json`| long context | claude-sonnet-4-5
| Math   | `math_longcontext_gpt-4.1-mini.json`| long context | gpt-4.1-mini
| Math   | `math_letta.json`| letta | gpt-5-mini
| Math   | `math_mem0.json`| mem0 | gpt-5-mini
| Math   | `math_mem0-g.json`| mem0-g | gpt-5-mini
| Math   | `math_mirix.json`| mirxi | gpt-5-mini
| Math   | `math_reasoningbank.json`| reasoningbank | gpt-5-mini
| Math   | `math_task_bm25.json`| bm25 | gpt-5-mini
| Math   | `math_task_text-embedding.json`| text-embedding-3-small | gpt-5-mini
| Math   | `math_task_memorag.json`| memorag | gpt-5-mini
| Math   | `math_task_graphrag.json`| graphrag | gpt-5-mini
| Math   | `math_agent_memory.json`| agent_memory | gpt-5-mini

Similarly for `phys`:
|Task| Config | Memory System | Model |
|--------|--------|--------------|-------|
| Phys   | `phys_longcontext_gpt-5-mini.json`| long context | gpt-5-mini
| Phys   | `phys_text-embedding.json`| text-embedding-3-small | gpt-5-mini
| Phys   | `phys_agent_memory.json`| agent_memory | gpt-5-mini
| Phys   | `phys_agent_memory_passive.json`| agent_memory_passive | gpt-5-mini
|... | ...| ...

You can add your configs accordingly. 