# DSPy + FastAPI Streaming Integration

researched: 2025-01-26
status: complete
tags: ai, llm, python, fastapi, streaming, dspy, server-sent-events

## Executive Summary

DSPy 2.6.0+ supports streaming responses via FastAPI using Server-Sent Events (SSE). This enables real-time token streaming, status updates during agent execution, and responsive AI applications.

## Background

Streaming allows AI applications to send partial responses to clients as they are generated, rather than waiting for complete responses. This improves perceived latency and enables real-time progress feedback for long-running operations like multi-step agent reasoning.

## Key Findings

### Installation

```bash
pip install -U dspy fastapi uvicorn
```

### Basic Non-Streaming Setup

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import dspy

app = FastAPI()

class Question(BaseModel):
    text: str

lm = dspy.LM("openai/gpt-4o-mini")
dspy.configure(lm=lm, async_max_workers=4)

dspy_program = dspy.asyncify(dspy.ChainOfThought("question -> answer"))

@app.post("/predict")
async def predict(question: Question):
    result = await dspy_program(question=question.text)
    return {"status": "success", "data": result.toDict()}
```

### Simple SSE Streaming

```python
from fastapi.responses import StreamingResponse
from dspy.utils.streaming import streaming_response

dspy_program = dspy.asyncify(dspy.ChainOfThought("question -> answer"))
streaming_program = dspy.streamify(dspy_program)

@app.post("/predict/stream")
async def stream(question: Question):
    stream = streaming_program(question=question.text)
    return StreamingResponse(
        streaming_response(stream),
        media_type="text/event-stream"
    )
```

### Custom SSE with Token Streaming

```python
import json

@app.post("/v1/query")
async def query_stream(question: Question):
    async def generate():
        async for item in streaming_program(question=question.text):
            if isinstance(item, dspy.streaming.StreamResponse):
                yield f"data: {json.dumps({'type': 'token', 'chunk': item.chunk})}\n\n"
            elif isinstance(item, dspy.streaming.StatusMessage):
                yield f"data: {json.dumps({'type': 'status', 'msg': item.message})}\n\n"
            elif isinstance(item, dspy.Prediction):
                yield f"data: {json.dumps({'type': 'result', 'answer': item.answer})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

### StreamListeners for Field Streaming

Stream specific output fields as tokens are generated:

```python
predict = dspy.Predict("question -> answer")

stream_predict = dspy.streamify(
    predict,
    stream_listeners=[
        dspy.streaming.StreamListener(signature_field_name="answer")
    ]
)
```

For agents with repeated fields (e.g., ReAct loops):

```python
stream_listeners = [
    dspy.streaming.StreamListener(
        signature_field_name="next_thought",
        allow_reuse=True  # Required for repeated field access
    )
]
```

### Status Message Streaming

Provide real-time status updates during agent execution:

```python
class MyStatusProvider(dspy.streaming.StatusMessageProvider):
    def tool_start_status_message(self, instance, inputs):
        return f"Calling {instance.name}..."

    def tool_end_status_message(self, outputs):
        return f"Done: {str(outputs)[:50]}"

    def lm_start_status_message(self, instance, inputs):
        return "Thinking..."

    def lm_end_status_message(self, outputs):
        return None  # Return None to skip message

    def module_start_status_message(self, instance, inputs):
        return f"Running {instance.__class__.__name__}..."

    def module_end_status_message(self, outputs):
        return None
```

### Full Combined Example

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import dspy
import json

app = FastAPI()

class Query(BaseModel):
    question: str

class AgentStatusProvider(dspy.streaming.StatusMessageProvider):
    def tool_start_status_message(self, instance, inputs):
        return f"Using tool: {instance.name}"

    def tool_end_status_message(self, outputs):
        return "Tool complete"

    def lm_start_status_message(self, instance, inputs):
        return "Generating response..."

def search(query: str) -> str:
    """Search for information."""
    return f"Results for: {query}"

react = dspy.ReAct("question -> answer", tools=[search])

streaming_agent = dspy.streamify(
    react,
    status_message_provider=AgentStatusProvider(),
    stream_listeners=[
        dspy.streaming.StreamListener(
            signature_field_name="next_thought",
            allow_reuse=True
        )
    ]
)

@app.post("/chat/stream")
async def chat_stream(query: Query):
    async def generate():
        async for item in streaming_agent(question=query.question):
            if isinstance(item, dspy.streaming.StatusMessage):
                yield f"data: {json.dumps({'type': 'status', 'message': item.message})}\n\n"
            elif isinstance(item, dspy.streaming.StreamResponse):
                yield f"data: {json.dumps({'type': 'token', 'field': item.signature_field_name, 'chunk': item.chunk})}\n\n"
            elif isinstance(item, dspy.Prediction):
                yield f"data: {json.dumps({'type': 'complete', 'answer': item.answer})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

### streamify API Reference

```python
dspy.streamify(
    program,                                    # DSPy module to wrap
    status_message_provider=None,               # StatusMessageProvider subclass
    stream_listeners=None,                      # list[StreamListener]
    include_final_prediction_in_output_stream=True,
    is_async_program=False,                     # True if already asyncified
    async_streaming=True                        # False for sync generator
)
```

**Returns:** Async generator yielding:
- `StreamResponse` - Token chunks (with `predict_name`, `signature_field_name`, `chunk`)
- `StatusMessage` - Progress updates (with `message`)
- `Prediction` - Final result

### Running the Server

```bash
export OPENAI_API_KEY="your-key"
uvicorn app:app --reload
```

## Practical Implications

- Use `dspy.asyncify()` to wrap programs for async operation before streaming
- `streamify()` adds streaming capability on top of asyncified programs
- Status providers give visibility into agent reasoning steps
- StreamListeners let you choose which output fields to stream
- SSE format (`data: ...\n\n`) is standard for real-time web applications

## Sources & Further Reading

- DSPy Streaming Tutorial: https://dspy.ai/tutorials/streaming/
- DSPy Deployment Guide: https://dspy.ai/tutorials/deployment/
- streamify API Reference: https://dspy.ai/api/utils/streamify/

## Open Questions

- Handling connection drops and reconnection
- Backpressure management for slow clients
- Best practices for error handling mid-stream
