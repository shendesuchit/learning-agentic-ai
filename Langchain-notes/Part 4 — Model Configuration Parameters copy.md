# Part 3D — Model Configuration Parameters (Part 1)

> **Module:** LangChain Fundamentals
>
> **Level:** Beginner Software Engineers
>
> **Objective:** Learn how to control the behavior of Large Language Models using configuration parameters such as Temperature, Max Tokens, Top P, and Stop Sequences. These parameters determine *how* a model generates responses without changing the underlying model itself.

---

# The Engineering Problem

Imagine you've built an AI application using GPT-4.1 through LangChain.

Everything works perfectly.

Your product manager now comes back with three different requirements.

### Requirement 1

> Build a creative story generator.

---

### Requirement 2

> Build a legal contract analyzer.

---

### Requirement 3

> Build an AI coding assistant.

All three applications use the **same language model**.

Should they all behave identically?

Obviously not.

A storytelling application should be imaginative.

A legal assistant should be precise.

A coding assistant should be deterministic and consistent.

If the model always behaved the same way, it wouldn't be useful across different applications.

This is why model providers expose **configuration parameters**.

These parameters allow developers to influence *how* the model generates text without retraining it.

---

# Understanding the Difference

Many beginners confuse these three concepts.

| Concept    | Purpose                                             |
| ---------- | --------------------------------------------------- |
| Model      | The intelligence itself (GPT, Claude, Gemini, etc.) |
| Prompt     | The instructions you provide                        |
| Parameters | Settings that control generation behavior           |

Think of them like driving a car.

```text
Car

↓

Engine

↓

Driver

↓

Driving Settings
```

The engine is the model.

The driver is your prompt.

The driving settings are parameters.

Changing the settings doesn't replace the engine—it changes how the engine behaves.

---

# Where Are Parameters Used?

When your application calls an LLM, the request contains more than just the prompt.

A typical API request looks conceptually like this:

```text
User Prompt

+

Temperature

+

Max Tokens

+

Top P

+

Stop Sequences

↓

LLM

↓

Generated Response
```

The model considers all these settings while generating each token.

---

# LangChain and Model Parameters

One of LangChain's goals is to provide a consistent interface across providers.

For example:

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4.1",
    temperature=0.2,
    max_tokens=500
)
```

Or with Anthropic:

```python
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(
    model="claude-3-sonnet",
    temperature=0.2
)
```

Notice something.

The provider changes.

The configuration pattern stays largely the same.

This is another example of LangChain's abstraction layer.

---

# The Most Important Parameter: Temperature

Whenever developers discuss LLM configuration, the first parameter they usually mention is **Temperature**.

Temperature controls the **randomness** of the model's output.

A lower temperature makes responses more predictable.

A higher temperature makes responses more varied and creative.

Importantly, temperature does **not** make the model "more intelligent."

It only changes how the model selects from its possible next-token predictions.

---

# Understanding Temperature with an Example

Suppose the prompt is:

```text
The capital of France is
```

The model internally assigns probabilities.

| Token  | Probability |
| ------ | ----------: |
| Paris  |         98% |
| Lyon   |          1% |
| London |         <1% |

At a very low temperature, the model almost always selects the highest-probability token.

Result:

```text
Paris
```

Every time.

---

Now consider a creative prompt.

```text
Write a fantasy kingdom name.
```

Possible predictions:

| Token    | Probability |
| -------- | ----------: |
| Eldoria  |         25% |
| Valoria  |         22% |
| Arcanis  |         18% |
| Drakmoor |         15% |

With a higher temperature, the model explores more of these alternatives, producing more diverse outputs.

---

# Real-World Analogy

Imagine a classroom.

The teacher asks:

> "Name a fruit."

### Student A

Always answers:

> Apple

Very consistent.

Very predictable.

---

### Student B

Answers:

* Mango
* Dragon Fruit
* Kiwi
* Pomegranate
* Passion Fruit

More creative.

Less predictable.

Temperature controls where the model falls on this spectrum.

---

# Temperature Scale

Although exact behavior differs slightly across providers, the general intuition is:

| Temperature | Behavior                     |
| ----------- | ---------------------------- |
| 0.0         | Nearly deterministic         |
| 0.2         | Highly consistent            |
| 0.5         | Balanced                     |
| 0.7         | More diverse                 |
| 1.0+        | Highly creative and variable |

Some providers allow values above 1.0, but higher values increase unpredictability.

---

# When to Use Low Temperature

Low temperature is ideal when consistency is important.

Examples:

* Code generation
* SQL generation
* Mathematical reasoning
* Legal analysis
* Medical documentation
* Data extraction
* Structured JSON output

In these applications, you generally want the same input to produce the same output.

---

# When to Use Higher Temperature

Higher temperatures are better suited for creative tasks.

Examples:

* Story writing
* Brainstorming
* Marketing copy
* Poetry
* Character generation
* Game dialogue
* Creative naming

Here, diversity is often more valuable than consistency.

---

# Common Beginner Mistake

Many people think:

> "Higher temperature means a smarter model."

It doesn't.

The model's knowledge and reasoning capabilities remain the same.

Temperature only influences how confidently or creatively it chooses among likely next tokens.

---

# Max Tokens

Another fundamental parameter is **Max Tokens**.

This parameter controls the maximum number of tokens the model is allowed to generate in its response.

It acts as an upper limit—not a target.

---

# Why Does Max Tokens Exist?

Imagine asking:

```text
Explain Python.
```

Without any limit, the model could generate thousands of words.

That creates several problems.

* Higher cost
* Longer response time
* More latency
* Unnecessary verbosity

Max Tokens helps control these factors.

---

# Example

```python
llm = ChatOpenAI(
    model="gpt-4.1",
    max_tokens=200
)
```

Here, the model can generate **up to** 200 output tokens.

If it finishes naturally after 120 tokens, it stops.

If it reaches 200 tokens before completing its thought, the response will be truncated.

---

# Input Tokens vs Output Tokens

It's important to distinguish between:

* **Input Tokens** — your prompt, system instructions, conversation history, retrieved documents, etc.
* **Output Tokens** — the model's generated response.

For example:

```text
Input

800 Tokens

↓

Model

↓

Output

200 Tokens
```

If your provider bills separately for input and output tokens, both contribute to the total cost.

---

# Common Misconception

Many beginners assume:

> Max Tokens controls the total request size.

It doesn't.

It controls only the maximum **generated output**.

The total context also includes the input tokens.

We'll revisit this when discussing context windows and pricing.

---

# Stop Sequences

Sometimes, you don't want the model to decide when to stop.

You want **your application** to decide.

This is where **Stop Sequences** become useful.

A stop sequence is a specific string that tells the model:

> "Stop generating when you reach this point."

---

# Example

Suppose you're generating structured text.

Prompt:

```text
Question:
What is LangChain?

Answer:
```

You specify:

```text
Stop Sequence:

Question:
```

Now, if the model begins generating another question, generation stops automatically before that point.

---

# Why Is This Useful?

Stop sequences are commonly used for:

* Prompt templates
* Structured outputs
* Multi-step agents
* Legacy completion models
* Preventing unwanted continuation

Although modern chat models rely less on manual stop sequences than older completion APIs, understanding them remains valuable because many providers and frameworks still support them.

---

# Architecture of a Generation Request

Putting everything together:

```text
                User Prompt
                     │
                     ▼
          +----------------------+
          | Model Parameters     |
          |----------------------|
          | Temperature          |
          | Max Tokens           |
          | Stop Sequences       |
          +----------------------+
                     │
                     ▼
                  LLM Engine
                     │
                     ▼
              Token-by-Token Generation
                     │
                     ▼
              Final Response
```

Notice that these parameters do not change the model itself.

They influence the **generation process** during inference.

---

# Production Best Practices

Experienced AI engineers rarely use the same parameter values for every application.

Typical approaches include:

| Application      | Suggested Temperature |
| ---------------- | --------------------: |
| Customer Support |               0.2–0.4 |
| Code Generation  |               0.0–0.2 |
| Data Extraction  |                   0.0 |
| SQL Generation   |                   0.0 |
| Creative Writing |               0.8–1.0 |
| Brainstorming    |               0.7–1.0 |

These are starting points, not universal rules. The optimal values depend on your application and should be validated through testing.

---

# Common Beginner Mistakes

### Setting Temperature Too High

This can make factual applications inconsistent.

---

### Using Very Low Temperature for Creative Tasks

Creative applications may produce repetitive or unimaginative results.

---

### Setting Max Tokens Too Small

Responses may be cut off before completing.

---

### Setting Max Tokens Excessively High

Higher limits can increase cost and latency, even if the model doesn't always use the full allowance.

---

# Key Takeaways

* Model parameters control **how** an LLM generates text; they do not change what the model has learned.
* **Temperature** adjusts randomness and creativity, while **Max Tokens** limits the maximum length of the generated response.
* **Stop Sequences** allow applications to terminate generation at predefined points.
* Different applications require different parameter settings based on their goals.
* Choosing good parameter values is part of prompt engineering and production optimization, not model training.

---

## Coming Up Next

In **Part 3D (Part 2)**, we'll explore more advanced configuration parameters used in production systems:

* **Top P (Nucleus Sampling)**
* **Top K Sampling**
* **Frequency Penalty**
* **Presence Penalty**
* **Seed & Deterministic Generation**
* **Streaming Responses**
* **JSON Mode**
* **Structured Output**
* **Response Format APIs**
* **Production tuning strategies**
* **Provider-specific differences (OpenAI vs Anthropic vs Gemini)**

This next section will move from basic configuration to the advanced controls used in real-world AI applications.
