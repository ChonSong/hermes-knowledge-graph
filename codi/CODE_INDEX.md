# Code Library Index

## Modules

| Module | Lines | Description |
|--------|-------|-------------|
| `cloudflare_dns.py` | 113 | Cloudflare DNS API client for CRUD operations on DNS records |
| `dnspod_client.py` | 234 | Tencent Cloud DNSPod API v3 client wrapper |
| `speedtest_ip.py` | 55 | Fetches optimized CDN IPs from speed test endpoints |
| `notifier.py` | 63 | PushPlus notification client for messaging |
| `portainer-templates/schema.json` | 226 | JSON Schema for Portainer app template v3 |
| `portainer-templates/combiner.py` | 250 | Template loader, normalizer, and deduplicator |
| `portainer-templates/downloader.py` | 120 | Download and enrich templates from external CSV sources |
| `portainer-templates/validator.py` | 119 | Schema validation for Portainer templates |
| `portainer-templates/generator.py` | 155 | Markdown documentation generator from templates |
| `tinker_model_info.py` | 134 | Model metadata registry for Llama, Qwen, DeepSeek, Kimi |
| `tinker_misc_utils.py` | 109 | Utilities: timed context manager, safezip, dict_mean, split_list |
| `tinker_tokenizer_utils.py` | 88 | Tokenizer factory with caching and custom registry |
| `tinker_rl_types.py` | 111 | RL core types: Env, EnvGroupBuilder, Trajectory, Transition |
| `tinker_dpo_loss.py` | 91 | Direct Preference Optimization loss computation |
| `tinker_checkpoint_utils.py` | 111 | Checkpoint management: save/load checkpoint records |
| `openhands_llm.py` | 292 | LLM wrapper using litellm with retry, metrics, function calling |
| `openhands_config.py` | 164 | Config loading from TOML and environment variables |
| `openhands_events.py` | 292 | Event system: Event, Action, Observation, EventStream |
| `openhands_fncall.py` | 247 | Function calling conversion for non-FC models |
| `nanobot_provider_registry.py` | 228 | LLM provider registry with auto-detection |
| `nanobot_memory.py` | 267 | Two-layer memory: MEMORY.md + HISTORY.md with consolidation |
| `nanobot_session.py` | 243 | Session management with JSONL persistence |
| `nanobot_tools.py` | 231 | Tool registry for dynamic agent tool management |
| `agentops_config.py` | 178 | Config with env var support, factory defaults |
| `agentops_telemetry.py` | 193 | OpenTelemetry setup with tracer/meter providers |
| `agentops_serialization.py` | 144 | JSON serialization helpers for special types |
| `agentops_events.py` | 290 | Event tracking: ActionEvent, LLMEvent, ErrorEvent |
| `langgraph_state.py` | 309 | StateGraph builder: nodes, edges, Send, Command, Interrupt |
| `langgraph_checkpoint.py` | 303 | Checkpoint types: Checkpoint, StateSnapshot, MemorySaver |
| `langgraph_pregel.py` | 360 | Pregel execution engine: streaming, interrupts, channels |

## Usage

### Cloudflare + DNSPod + SpeedTest

```python
from cloudflare_dns import CloudflareDNS
from dnspod_client import DNSPodClient
from speedtest_ip import fetch_best_ips
from notifier import PushNotifier
import os

ips = fetch_best_ips()
if ips:
    cf = CloudflareDNS(os.getenv('CF_API_TOKEN'), os.getenv('CF_ZONE_ID'))
    cf.sync_to_best_ip("dns.example.com", ips)
    dnspod = DNSPodClient(os.getenv('SECRETID'), os.getenv('SECRETKEY'))
    notifier = PushNotifier(os.getenv('PUSHPLUS_TOKEN'))
```

### Tinker Cookbook ML Utils

```python
from tinker_model_info import get_model_attributes
from tinker_tokenizer_utils import get_tokenizer
from tinker_dpo_loss import compute_dpo_loss
```

### OpenHands Agent Utils

```python
from openhands_llm import LLMWrapper, LLMConfig
from openhands_config import ConfigBase
from openhands_events import EventStream
from openhands_fncall import inject_function_calling_prompt
```

### Nanobot Agent Patterns

```python
from nanobot_provider_registry import detect_provider
from nanobot_memory import TwoLayerMemory
from nanobot_session import SessionManager
from nanobot_tools import ToolRegistry
```

### AgentOps Patterns

```python
from agentops_config import Config
from agentops_telemetry import setup_telemetry
from agentops_serialization import safe_serialize
from agentops_events import EventRecorder
```

### LangGraph Patterns

```python
from langgraph_state import StateGraph, Send, Command, add_messages
from langgraph_checkpoint import MemorySaver, Checkpoint, RunnableConfig
from langgraph_pregel import Pregel, StreamMode

# Define state
from typing_extensions import TypedDict, Annotated
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    count: int

# Build graph
graph = StateGraph(AgentState)
graph.add_node("process", process_node)
graph.add_edge("__start__", "process")
graph.add_edge("process", "__end__")

# Compile with checkpointing
app = graph.compile(checkpointer=MemorySaver())

# Run with persistence
result = app.invoke(
    {"messages": ["hi"]},
    config={"configurable": {"thread_id": "my-thread"}}
)
```

## Sources

- `ZhiXuanWang/cf-speed-dns` - Cloudflare DNS
- `Lissy93/portainer-templates` - Portainer Templates
- `thinking-machines-lab/tinker-cookbook` - Tinker ML Utils
- `All-Hands-AI/OpenHands` - OpenHands Agent
- `HKUDS/nanobot` - Nanobot Agent
- `agentops/agentops` - AgentOps (via PyPI)
- `langchain-ai/langgraph` - LangGraph StateGraph & Checkpointing