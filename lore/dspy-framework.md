# DSPy Framework for Modular AI Systems

researched: 2025-01-26
status: complete
tags: ai, llm, python, machine-learning, prompt-engineering, agents

## Executive Summary

DSPy is a Stanford NLP framework for building modular AI systems through structured programming rather than prompt engineering. It compiles Python code into effective prompts, supports automatic optimization, and provides building blocks for agents, RAG systems, and complex AI pipelines.

## Background

The core philosophy of DSPy is "Programming--not prompting--LMs." Instead of crafting brittle prompt strings, you write structured code using Signatures and Modules that DSPy compiles into effective prompts. The framework handles prompt generation, parsing, and can automatically optimize prompts based on evaluation metrics.

## Key Findings

### Installation and Quick Start

```bash
pip install -U dspy
```

```python
import dspy

lm = dspy.LM('openai/gpt-4o-mini')
dspy.configure(lm=lm)

qa = dspy.ChainOfThought('question -> answer')
result = qa(question="What is the capital of France?")
print(result.answer)
```

### Language Models

DSPy supports many providers via LiteLLM:

```python
# OpenAI
lm = dspy.LM('openai/gpt-4o-mini', api_key='...')

# Anthropic
lm = dspy.LM('anthropic/claude-3-opus', api_key='...')

# Local (Ollama)
lm = dspy.LM('ollama/llama3.2')

# Configure globally
dspy.configure(lm=lm)

# Or use context for scoped changes (thread-safe)
with dspy.context(lm=other_lm):
    result = module(input="...")
```

### Signatures

Signatures define input/output behavior declaratively.

**Inline signatures:**
```python
"question -> answer"
"question: str -> answer: str"
"sentence -> sentiment: bool"
"context: list[str], question: str -> answer: str"
```

**Class-based signatures (for complex tasks):**
```python
from typing import Literal

class Emotion(dspy.Signature):
    """Classify the emotion in a sentence."""
    sentence: str = dspy.InputField()
    sentiment: Literal['sadness', 'joy', 'anger', 'fear'] = dspy.OutputField()
```

Supported types: `str`, `int`, `bool`, `float`, `list[...]`, `dict[...]`, `Optional[...]`, `Literal[...]`, `dspy.Image`, Pydantic models

### Modules

Modules are building blocks that abstract prompting techniques.

| Module | Purpose |
|--------|---------|
| `dspy.Predict` | Basic prediction |
| `dspy.ChainOfThought` | Step-by-step reasoning before answering |
| `dspy.ProgramOfThought` | Generate code to compute answers |
| `dspy.ReAct` | Agent with tool usage |
| `dspy.MultiChainComparison` | Compare multiple reasoning chains |

**Custom modules:**
```python
class MultiHopQA(dspy.Module):
    def __init__(self, num_hops=3):
        self.num_hops = num_hops
        self.generate_query = dspy.ChainOfThought("context, question -> query")
        self.generate_answer = dspy.ChainOfThought("context, question -> answer")

    def forward(self, question):
        context = []
        for _ in range(self.num_hops):
            query = self.generate_query(context=context, question=question).query
            context.extend(retrieve(query))
        return self.generate_answer(context=context, question=question)
```

### Building Agents

**Define tools as Python functions with clear docstrings:**
```python
def get_weather(city: str, units: str = "celsius") -> str:
    """Get current weather for a city.

    Args:
        city: Name of the city
        units: Temperature units (celsius or fahrenheit)
    """
    return f"Weather in {city}: 22 degrees {units}"
```

**ReAct Agent:**
```python
agent = dspy.ReAct(
    signature="question -> answer",
    tools=[calculator, search],
    max_iters=10
)

result = agent(question="What is the population of the capital of France?")
print(result.answer)
print(result.trajectory)  # reasoning and action history
```

### Evaluation

```python
# Build datasets
trainset = [
    dspy.Example(question="What is 2+2?", answer="4"),
    dspy.Example(question="Capital of Japan?", answer="Tokyo"),
]

# Define metrics
def exact_match(example, prediction, trace=None):
    return example.answer.lower() == prediction.answer.lower()

# Run evaluation
from dspy.evaluate import Evaluate
evaluator = Evaluate(devset=devset, metric=exact_match, num_threads=4)
score = evaluator(my_program)
```

### Optimization

Optimizers automatically tune prompts and demonstrations based on metrics.

| Optimizer | Use Case |
|-----------|----------|
| `BootstrapFewShot` | Basic few-shot learning |
| `BootstrapFewShotWithRandomSearch` | Few-shot with exploration |
| `MIPROv2` | Joint instruction + example optimization |
| `COPRO` | Instruction optimization |
| `GEPA` | Advanced reflective evolution |

**Using MIPROv2:**
```python
from dspy.teleprompt import MIPROv2

optimizer = MIPROv2(
    metric=exact_match,
    auto="medium",  # "light", "medium", or "heavy"
    num_trials=30,
)

optimized_program = optimizer.compile(
    student=my_program,
    trainset=trainset,
)

optimized_program.save("optimized_qa.json")
```

### Common Patterns

**RAG:**
```python
class RAG(dspy.Module):
    def __init__(self, num_docs=3):
        self.retrieve = your_retriever
        self.generate = dspy.ChainOfThought("context, question -> answer")

    def forward(self, question):
        docs = self.retrieve(question, k=self.num_docs)
        context = "\n".join(docs)
        return self.generate(context=context, question=question)
```

**Classification:**
```python
class Classifier(dspy.Signature):
    """Classify text into categories."""
    text: str = dspy.InputField()
    category: Literal['tech', 'sports', 'politics', 'other'] = dspy.OutputField()

classify = dspy.Predict(Classifier)
```

## Practical Implications

1. **Start simple** - Begin with `dspy.Predict` or `dspy.ChainOfThought`, add complexity based on results
2. **Use descriptive field names** - Signatures work better with semantic names (`customer_query` vs `input`)
3. **Write clear tool docstrings** - Agents rely on descriptions to choose tools
4. **Iterate on metrics** - Your evaluation metric drives optimization
5. **Test with powerful models first** - Understand what's achievable, then optimize for smaller models
6. **Data split for optimization** - Use 20% training, 80% validation to prevent overfitting

## Sources & Further Reading

- Documentation: https://dspy.ai
- GitHub: https://github.com/stanfordnlp/dspy
- Discord: https://discord.gg/XCGy2WDCQB
- Tutorials: https://dspy.ai/tutorials/

## Open Questions

- Best strategies for handling very long contexts
- How to effectively debug optimization failures
- Patterns for combining multiple optimized modules
