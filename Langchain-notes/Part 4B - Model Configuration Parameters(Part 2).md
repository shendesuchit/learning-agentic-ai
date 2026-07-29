# Part 4 — Model Configuration Parameters (Part 2)

> **Module:** LangChain Fundamentals
>
> **Level:** Beginner to Intermediate
>
> **Objective:** Learn the advanced model configuration parameters used in production AI systems, including **Top P, Top K, Frequency Penalty, Presence Penalty, Seed, Streaming, JSON Mode, Structured Output, and Production Tuning Strategies**.

---

# The Engineering Problem

In Part 4 (Part 1), we learned that **Temperature** controls randomness.

Many beginners assume that this is the only parameter needed.

However, once you begin building production AI applications, you'll encounter scenarios like these:

* "The model keeps repeating the same sentence."
* "I need the output in valid JSON every time."
* "I want users to see words appearing as they're generated."
* "I need identical responses for automated testing."
* "I want more diversity without making responses nonsensical."

Temperature alone cannot solve these problems.

Modern LLM APIs expose additional parameters that give developers much finer control over text generation.

Understanding these parameters is essential for building reliable AI systems.

---

# Recap: How an LLM Generates Text

Before introducing new parameters, let's briefly revisit how generation works.

When you send a prompt, the model predicts probabilities for the next token.

For example:

```text
Prompt:
The capital of France is
```

Internal prediction:

| Token  | Probability |
| ------ | ----------: |
| Paris  |         98% |
| Lyon   |          1% |
| London |        0.5% |
| Berlin |        0.2% |
| Madrid |        0.1% |

The model then selects one of these tokens.

Temperature influences this selection.

But it isn't the only mechanism.

---

# Top P (Nucleus Sampling)

One of the most widely used generation parameters is **Top P**.

Top P controls **how many candidate tokens are considered** before selecting the next token.

Instead of looking at every possible token in the vocabulary, the model builds a shortlist whose cumulative probability reaches a threshold **P**.

This technique is called **Nucleus Sampling**.

---

# Why Does Top P Exist?

Imagine the model predicts these probabilities.

| Token     | Probability |
| --------- | ----------: |
| Paris     |         60% |
| Lyon      |         20% |
| Marseille |         10% |
| London    |          5% |
| Berlin    |          3% |
| Tokyo     |          2% |

Suppose:

```text
Top P = 0.90
```

The model begins adding tokens:

```text
Paris

↓

60%
```

Still below 90%.

Add Lyon.

```text
Paris

+

Lyon

↓

80%
```

Still below 90%.

Add Marseille.

```text
Paris

+

Lyon

+

Marseille

↓

90%
```

Now the threshold has been reached.

The remaining tokens are ignored.

The next token will be selected only from:

* Paris
* Lyon
* Marseille

---

# Real-World Analogy

Imagine participating in a job interview.

One hundred candidates apply.

The company decides:

> "We'll interview only candidates who collectively represent the top 90% of qualifications."

The remaining applicants are never considered.

Top P works similarly.

Instead of evaluating every possible token, it focuses on the most probable subset.

---

# Temperature vs Top P

These parameters are often confused.

They influence different parts of the sampling process.

### Temperature

Changes the probability distribution itself.

### Top P

Limits which tokens are eligible for selection.

Think of it this way.

Temperature changes **how adventurous the model is**.

Top P changes **how many choices the model is allowed to consider**.

---

# Should You Use Both?

Most providers recommend adjusting **either Temperature or Top P**, not both aggressively at the same time.

Why?

Because both influence randomness.

Changing both simultaneously can make behavior difficult to predict.

A common production approach is:

* Tune Temperature
* Leave Top P at its default

Or:

* Keep Temperature fixed
* Experiment with Top P

---

# Top K Sampling

Some providers also expose another parameter called **Top K**.

Instead of selecting tokens based on cumulative probability,

Top K selects the **K highest-probability tokens**.

Example:

```text
Top K = 5
```

Only the five most probable tokens remain candidates.

Everything else is discarded.

---

# Top K Example

Model predictions:

| Token     | Probability |
| --------- | ----------: |
| Paris     |         45% |
| Lyon      |         20% |
| Marseille |         15% |
| London    |          8% |
| Berlin    |          5% |
| Madrid    |          3% |
| Tokyo     |          2% |

With:

```text
Top K = 3
```

Only:

* Paris
* Lyon
* Marseille

remain eligible.

The others are ignored.

---

# Top P vs Top K

| Top P                              | Top K                         |
| ---------------------------------- | ----------------------------- |
| Uses cumulative probability        | Uses a fixed number of tokens |
| Dynamic shortlist                  | Fixed shortlist               |
| Adapts to probability distribution | Always considers K tokens     |
| More common in modern APIs         | Less commonly exposed         |

Many modern commercial APIs hide Top K entirely because Top P generally produces smoother behavior.

---

# Frequency Penalty

Another common issue appears during long generations.

Sometimes the model repeats itself.

Example:

```text
Python is easy.

Python is powerful.

Python is popular.

Python is flexible.

Python is amazing.

Python...
```

Repeated words reduce output quality.

This is where **Frequency Penalty** helps.

---

# What Is Frequency Penalty?

Frequency Penalty reduces the probability of tokens that have already appeared frequently in the generated response.

The more often a word appears,

the less likely it becomes to appear again.

---

# Example

Without penalty:

```text
AI is powerful.

AI is useful.

AI is transforming industries.

AI...
```

With Frequency Penalty:

```text
Artificial Intelligence is powerful.

This technology is useful.

It is transforming industries.
```

Notice the increased variety.

---

# Best Use Cases

Frequency Penalty is useful for:

* Long-form writing
* Story generation
* Blog creation
* Marketing content
* Report generation

It helps reduce repetitive phrasing.

---

# Presence Penalty

Presence Penalty is related to Frequency Penalty but solves a different problem.

Instead of counting **how often** a token appears,

Presence Penalty only asks:

> Has this token appeared before?

If yes,

reduce its likelihood.

---

# Frequency vs Presence

Suppose the word "Python" appears.

### Frequency Penalty

Counts:

```text
Python

Python

Python

Python
```

The more occurrences,

the stronger the penalty.

---

### Presence Penalty

Only checks:

```text
Has "Python" appeared?

Yes.
```

Penalty applied.

Whether it appeared once or twenty times doesn't matter.

---

# Simple Analogy

Imagine a teacher.

Frequency Penalty says:

> "You've already spoken five times.
> Let someone else speak."

Presence Penalty says:

> "You've already spoken once.
> Let's hear from someone new."

---

# Seed (Deterministic Generation)

AI outputs are usually probabilistic.

Even with the same prompt,

results may vary slightly.

Some providers expose a **Seed** parameter.

A seed initializes the random sampling process.

Using the same:

* model
* prompt
* parameters
* seed

can make responses more reproducible.

---

# Why Is Seed Useful?

Imagine writing automated tests.

You don't want today's output to differ from tomorrow's.

A fixed seed increases consistency.

However,

reproducibility is not always guaranteed across model updates or provider infrastructure changes.

---

# Streaming Responses

Suppose you ask ChatGPT:

> "Explain Quantum Computing."

Do you notice something?

The answer doesn't appear all at once.

Instead,

words arrive gradually.

This is called **Streaming**.

---

# Normal Response

```text
Request

↓

Wait

↓

Entire Response
```

---

# Streaming Response

```text
Request

↓

Token

↓

Token

↓

Token

↓

Token

↓

Complete Response
```

Streaming improves the user experience because users begin reading before generation finishes.

---

# Why Streaming Matters

Without streaming:

* Higher perceived latency
* Blank waiting screen

With streaming:

* Faster perceived performance
* Better conversational experience
* Progressive rendering

This is why almost every modern AI chatbot streams responses.

---

# JSON Mode

Many applications don't need paragraphs.

They need structured data.

Example:

Instead of:

> "John is 25 years old."

Your application needs:

```json
{
  "name": "John",
  "age": 25
}
```

JSON Mode tells the model to generate valid JSON instead of free-form text.

---

# Why JSON Mode Exists

Suppose your application parses responses automatically.

Natural language is difficult to parse reliably.

JSON is much easier.

Example workflow:

```text
User

↓

LLM

↓

JSON

↓

Python Object

↓

Business Logic
```

Modern AI applications heavily rely on structured outputs.

---

# Structured Output

JSON Mode guarantees syntax.

Structured Output goes one step further.

Instead of merely producing JSON,

the model follows a predefined schema.

Example schema:

```json
{
  "customer_name": "string",
  "email": "string",
  "priority": "low | medium | high"
}
```

The model attempts to populate these fields while respecting the expected structure.

This dramatically reduces parsing errors and simplifies downstream application logic.

---

# JSON Mode vs Structured Output

| JSON Mode             | Structured Output               |
| --------------------- | ------------------------------- |
| Valid JSON            | JSON following a defined schema |
| Flexible              | Strict field definitions        |
| Easier parsing        | Easier validation               |
| Good for general APIs | Best for production systems     |

Whenever your application depends on predictable machine-readable output, structured output is generally the preferred approach.

---

# Putting It All Together

A production request may include several parameters.

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4.1",
    temperature=0.2,
    max_tokens=500,
    top_p=0.9
)
```

Depending on the provider, additional options such as streaming or structured output may be configured through the client or invocation methods rather than the constructor.

The exact API varies by provider, but the concepts remain the same.

---

# Production Tuning Strategies

Experienced AI engineers rarely pick parameter values arbitrarily.

Instead, they optimize for the application's requirements.

### Customer Support Bot

* Low Temperature
* Moderate Max Tokens
* Structured Output
* Streaming Enabled

---

### Coding Assistant

* Temperature near 0
* High Context Window
* Streaming Enabled

---

### Marketing Content Generator

* Higher Temperature
* Moderate Top P
* Frequency Penalty

---

### Data Extraction Pipeline

* Temperature = 0
* Structured Output
* JSON Mode

---

### Research Assistant

* Moderate Temperature
* Larger Max Tokens
* Streaming
* Structured Output

---

# Provider Differences

Although concepts are similar across providers, the available parameters differ.

For example:

* Some providers expose **Top K**, while others do not.
* Some support **Seed**, while others don't guarantee reproducibility.
* Structured output APIs vary in implementation.
* Streaming is widely supported but configured differently.

LangChain helps abstract many of these differences, but developers should still consult the provider's documentation for provider-specific capabilities.

---

# Common Beginner Mistakes

### Adjusting Every Parameter at Once

Changing multiple sampling parameters simultaneously makes it difficult to understand which setting caused a behavior change.

---

### Assuming Higher Randomness Is Better

Creative settings are useful for storytelling but can reduce consistency in factual or code-generation tasks.

---

### Ignoring Structured Output

Parsing natural language when structured output is available often leads to unnecessary complexity.

---

### Expecting Seed to Guarantee Identical Outputs Forever

Provider updates, infrastructure changes, or model revisions can still affect generated responses.

---

### Forgetting the User Experience

Streaming doesn't make the model faster—it makes the application *feel* faster by showing partial output immediately.

---

# Official References

* LangChain Chat Models Documentation
* OpenAI Responses API Documentation
* Anthropic Messages API Documentation
* Google Gemini API Documentation

---

# Key Takeaways

* **Top P** limits token selection to the most probable cumulative set of candidates.
* **Top K** restricts sampling to a fixed number of high-probability tokens (when supported).
* **Frequency Penalty** reduces repetitive wording based on how often tokens have already appeared.
* **Presence Penalty** encourages introducing new concepts by discouraging reuse of previously seen tokens.
* **Seed** can improve reproducibility for testing, though exact determinism is not always guaranteed.
* **Streaming** improves perceived responsiveness by returning tokens as they are generated.
* **JSON Mode** ensures syntactically valid JSON, while **Structured Output** enforces a predefined schema.
* Effective production tuning is about selecting parameters that match the application's goals rather than maximizing every setting.

---

## Interview Perspective

A common interview question is:

> **"What is the difference between Temperature, Top P, Frequency Penalty, and Presence Penalty?"**

A strong answer would explain:

* **Temperature** controls randomness in token selection.
* **Top P** limits the candidate token pool based on cumulative probability.
* **Frequency Penalty** discourages repeating the same words multiple times.
* **Presence Penalty** encourages introducing new topics by penalizing tokens that have appeared at least once.

Understanding not just *what* these parameters do, but *why* they exist and *when* to use them, is a hallmark of engineers who build reliable production AI systems.

---

## Next Learning Step

With model configuration complete, the next logical chapter is:

# **Part 5 — Prompt Engineering Fundamentals**

We'll move from controlling the **model's behavior** to controlling the **model's reasoning** through prompts. Topics will include:

* What is Prompt Engineering?
* System, User, and Assistant Messages
* Chat Message Architecture
* Role-based prompting
* Zero-shot, One-shot, and Few-shot prompting
* Prompt Templates in LangChain
* Dynamic prompts
* Prompt injection and prompt security
* Production prompt engineering best practices

This is where you'll begin learning how professional AI engineers consistently guide LLMs toward accurate, reliable, and context-aware outputs.
