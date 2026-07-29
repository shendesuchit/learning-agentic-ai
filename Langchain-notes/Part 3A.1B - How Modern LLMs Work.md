# Part 3A.1 (Continued) — Tokens, Context Windows, Training vs Inference & Foundation Models

> **Module:** LangChain Fundamentals
>
> **Level:** Beginner Software Engineers
>
> **Objective:** Understand how LLMs actually "read" text, why they use tokens instead of words, what a context window is, and how training differs from inference.

---

# If LLMs Predict the Next Token...

In the previous section, we learned that every Large Language Model has one core objective:

> **Predict the next token.**

Notice something interesting.

We didn't say:

> Predict the next **word**.

We specifically said:

> Predict the next **token**.

This isn't a random choice of terminology.

Understanding tokens is one of the most important concepts in AI engineering because **every model provider charges, limits, and measures usage in tokens—not words.**

Before we discuss pricing, context windows, or model limits, we first need to understand what a token actually is.

---

# What Is a Token?

Most beginners assume that an LLM reads text exactly like humans do.

Humans naturally think in words.

For example:

```text
I love LangChain
```

We immediately recognize three words:

* I
* love
* LangChain

A computer doesn't.

Before an LLM can process language, the text must first be broken into smaller pieces called **tokens**.

---

# Think Like a Computer

Imagine someone hands you a book written in Japanese.

If you don't know Japanese, the book looks like random symbols.

Before understanding it, you'd first need to split it into recognizable units.

LLMs face the same problem.

Computers don't inherently understand:

* letters
* words
* grammar
* meaning

Everything must first become numbers.

Tokens are the bridge between **human language** and **machine computation**.

---

# Words vs Tokens

People often think:

```text
1 Word = 1 Token
```

Unfortunately, that's not true.

Consider this sentence.

```text
Hello world!
```

It might become something like:

```text
Hello

world

!
```

Three tokens.

Now consider:

```text
unbelievable
```

Instead of one token, it might become:

```text
un

believ

able
```

Three tokens.

Now consider:

```text
ChatGPT
```

Depending on the tokenizer, it might become:

```text
Chat

G

PT
```

or

```text
ChatGPT
```

There is no guarantee.

Tokens are determined by the model's tokenizer—not by English grammar.

---

# Why Not Use Words?

Imagine supporting every language on Earth.

Some languages use spaces.

Others don't.

Chinese, for example, doesn't separate every word with spaces the way English does.

Programming languages are different again.

Consider Python.

```python
print("Hello")
```

Should this become:

```text
print

(

"

Hello

"

)
```

or something else?

Different programming languages have different syntax.

Different human languages have different grammar.

Instead of inventing language-specific rules, model developers use tokenization algorithms that work across many languages and text formats.

---

# Tokenization

The process of converting text into tokens is called **tokenization**.

It happens before the model sees your prompt.

The overall flow looks like this:

```text
User Prompt

↓

Tokenizer

↓

Tokens

↓

Numbers

↓

LLM

↓

Output Tokens

↓

Detokenizer

↓

Human Readable Text
```

Notice something important.

The LLM never directly processes words.

It processes **numbers representing tokens**.

---

# Inside the Tokenizer

Imagine the sentence:

```text
I love AI
```

The tokenizer might convert it into something like:

```text
"I"

↓

245
```

```text
"love"

↓

8321
```

```text
"AI"

↓

415
```

Now the model doesn't receive text.

It receives:

```text
245

8321

415
```

Everything inside the neural network operates on numerical representations.

This is one reason machine learning is built on mathematics rather than linguistics.

---

# Every Provider Has Its Own Tokenizer

This surprises many beginners.

OpenAI,

Anthropic,

Google,

Meta,

Mistral,

DeepSeek—

they don't necessarily tokenize text the same way.

The exact same sentence may produce different token counts depending on the model.

That means:

100 words

≠

100 tokens

across every provider.

This becomes important when estimating:

* pricing
* latency
* context usage

---

# Why Developers Care About Tokens

From a software engineering perspective, tokens affect almost everything.

Providers bill based on:

* input tokens
* output tokens

Models also have limits based on tokens.

Even response speed is influenced by token generation.

When building production AI systems, engineers think in tokens—not words.

---

# A Practical Example

Suppose your prompt contains:

* 800 input tokens

The model generates:

* 200 output tokens

Total usage:

```text
800 Input Tokens

+

200 Output Tokens

=

1000 Total Tokens
```

Most providers charge separately for:

* input tokens
* output tokens

We'll compare provider pricing later in this chapter.

---

# The Context Window Problem

Imagine talking to someone.

You ask:

> What's my name?

They answer:

> Your name is Rahul.

Five hours later you ask:

> What's my name again?

A human remembers.

But what about an LLM?

Can it remember forever?

No.

Every model has a limited amount of information it can consider at one time.

This limit is called the **Context Window**.

---

# What Is a Context Window?

A context window is the maximum number of tokens a model can process in a single request.

Think of it as the model's short-term working memory.

Everything inside the window is visible.

Everything outside it is invisible.

---

# A Real-Life Analogy

Imagine writing on a whiteboard.

The board can only hold:

100 lines.

Once it fills up,

you must erase older content before writing more.

The whiteboard represents the context window.

---

# Visualizing Context

```text
Conversation

↓

Message 1

↓

Message 2

↓

Message 3

↓

...

↓

Latest Message
```

The model only sees what fits inside its context window.

Older messages eventually fall out.

---

# Why Context Matters

Suppose you ask:

```text
My favorite language is Python.
```

Later you ask:

```text
What's my favorite language?
```

If both messages are still inside the context window,

the model answers:

```text
Python
```

If the first message has fallen outside the context window,

the model has no memory of it.

This is why long conversations sometimes appear to "forget" earlier details.

---

# Does the Model Actually Remember?

This is another common misconception.

Many beginners believe ChatGPT permanently remembers every conversation.

It doesn't.

What actually happens is simpler.

For each request,

the application sends a portion of the conversation back to the model.

For example,

```text
User Message

↓

Assistant Reply

↓

User Message

↓

Assistant Reply

↓

Current Question
```

The entire conversation history (or part of it) is included in the new request.

The model doesn't retrieve memories.

It simply reads the supplied context again.

---

# Where Does Memory Come From Then?

This leads to an important distinction.

The LLM itself does **not** provide long-term memory.

Instead,

the **application** provides memory.

For example:

```text
User

↓

LangChain

↓

Conversation Memory

↓

LLM
```

This connects directly to something we learned in Part 1.

Remember?

```text
Agent

=

Model

+

Harness
```

Memory is part of the **Harness**.

Not the Model.

This is why frameworks like LangChain provide memory abstractions.

---

# Training vs Inference

This is one of the most misunderstood concepts in AI.

Many beginners think:

> Every time I chat with GPT,
> it's learning from me.

It isn't.

Let's separate two completely different phases.

---

# Phase 1 — Training

Training is when engineers teach the model.

During training:

* massive datasets are processed
* billions of parameters are adjusted
* weeks or months of computation occur
* thousands of GPUs are used

Training happens **before** the model is released.

Users are not involved.

---

# Phase 2 — Inference

Inference begins after training finishes.

Inference simply means:

> Using the trained model to make predictions.

Every ChatGPT conversation is inference.

Every Claude conversation is inference.

Every Gemini conversation is inference.

The model isn't learning.

It's applying what it already learned.

---

# Training vs Inference

| Training                       | Inference                      |
| ------------------------------ | ------------------------------ |
| Learn patterns                 | Use patterns                   |
| Extremely expensive            | Relatively inexpensive         |
| Months                         | Seconds                        |
| Massive GPU clusters           | Single API request             |
| Adjust parameters              | Parameters stay fixed          |
| Happens once (or periodically) | Happens for every user request |

This distinction is essential because **LangChain only interacts with models during inference**.

LangChain does **not** train models.

It orchestrates requests to already-trained models.

---

# What Is a Foundation Model?

Earlier, we mentioned that modern AI systems are built on **Foundation Models**.

What does that mean?

Imagine constructing a skyscraper.

You don't begin with the 50th floor.

You begin with the foundation.

Everything else is built on top.

Similarly,

Foundation Models are large, general-purpose models trained on enormous datasets.

They serve as the base for many downstream applications.

Examples include:

* GPT
* Claude
* Gemini
* Llama
* Mistral

These models aren't trained specifically for:

* customer support
* legal analysis
* medical advice
* coding
* education

Instead, they're designed to be adaptable to many different tasks through prompting, fine-tuning, or additional context.

---

# Why Foundation Models Changed AI

Before foundation models, companies often built a separate model for every problem:

```text
Spam Detection Model

↓

Translation Model

↓

Question Answering Model

↓

Sentiment Analysis Model
```

Each required its own:

* dataset
* training process
* infrastructure

Foundation models changed this dramatically.

Now, one general-purpose model can power many different applications simply by changing:

* the prompt
* the context
* the tools
* the surrounding application logic

This shift is one of the reasons frameworks like LangChain became so valuable—they provide the harness around these increasingly capable foundation models.

---

# Coming Up Next

In the next section of **Part 3A**, we'll move from understanding **what language models are** to understanding **the different types of models you'll encounter in practice**:

* Base Models vs Instruct Models
* Completion Models vs Chat Models
* Why Chat Models became the industry standard
* Why LangChain primarily works with Chat Models
* Message-based APIs and conversation architecture
* Internal request lifecycle
* Production architecture for modern LLM applications

These concepts will prepare us for **Part 3B**, where we'll compare real-world providers like **OpenAI, Anthropic, Gemini, Groq, Ollama, OpenRouter, and others**, and understand how LangChain abstracts them behind a common interface.
