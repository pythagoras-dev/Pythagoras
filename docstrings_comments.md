# Pythagoras docstrings and comments guidelines

This document defines the standards for writing docstrings and comments
in the `Pythagoras` project. Following these guidelines ensures
consistency, maintainability, and clarity across the codebase.

---
## Essentials Cheat Sheet

```yaml
# Quick Reference for Humans & LLMs

docstring_style: "Google-style (not NumPy or Sphinx)"

core_principles:
  - "Follow PEP 257 (Docstrings) and PEP 8 (Style)"
  - "Focus on WHAT and WHY, not HOW (unless non-obvious)"
  - "Use type hints in signatures, not in docstrings"
  - "Write for readers who understand Python but not this codebase"
  - "Be precise and concise, avoid creating noise"

always_document:
  - "Public modules (top of file)"
  - "Public classes"
  - "Public functions and methods"
  - "Complex private functions with non-trivial logic"

may_omit_docstrings:
  - "Trivial private helpers with clear names"
  - "Obvious dunder methods (__repr__, __str__)"
  - "Test functions (though brief docstrings help)"

docstring_section_order:
  1: "One-line summary"
  2: "Extended description (optional)"
  3: "Args: (functions/methods)"
  4: "Attributes: (classes)"
  5: "Returns: or Yields:"
  6: "Raises:"
  7: "Example: or Examples: (optional)"
  8: "Note: or Warning: (if needed)"

critical_dos:
  - "Use triple quotes for all docstrings (even one-liners)"
  - "Explain parameter purpose, not just type"
  - "Document WHY design choices were made"
  - "Keep docstrings focused on contract and intent"
  - "Use plain text references (no :class:, :meth: reST roles)"

critical_donts:
  - "Don't duplicate type info from type hints in docstrings"
  - "Don't explain obvious code with comments"
  - "Don't leave commented-out code blocks"
  - "Don't use inline tool directives (# type: ignore, # pylint:)"
  - "Don't over-explain trivial HOW (focus on non-obvious HOW)"

comments:
  purpose: "Clarify intent, reasoning, non-obvious behavior"
  inline: "Use sparingly; explain WHY or non-obvious WHAT"
  block: "For complex algorithms, edge cases, design decisions"
  tags: "TODO, FIXME, NOTE (with issue # if applicable)"
  avoid: "Obvious statements, trivial HOW, commented-out code"
```

---

## Core principles

1. **Use Google-style docstrings** for all public modules, classes,
   methods, and functions.
2. **Follow PEP 257** (Docstring Conventions) and **PEP 8** (Style
   Guide for Python Code).
3. **Focus on WHAT and WHY** in comments and docstrings. Explain HOW
   only when the implementation is non-obvious or uses advanced
   techniques. Typically, docstrings and comments should explain code
   intent and implementation strategies, not implementation details
4. **Write for the reader**: assume the reader understands Python but
   may be unfamiliar with this specific codebase.

---

## Docstrings

### When to write docstrings

**Always provide docstrings for:**
- Public modules (at the top of the file)
- Public classes
- Public functions and methods
- Non-trivial private functions that implement complex logic

**You may omit docstrings for:**
- Trivial private helper functions with self-explanatory names (e.g.,
  `_is_valid_key`)
- Standard dunder methods like `__repr__`, `__str__` when behavior is
  obvious
- Test functions (though a brief one-liner can help clarify intent)

### Google-style docstring format

Google-style docstrings are clean, readable, and well-supported by
documentation tools like Sphinx (with the Napoleon extension).

#### Basic structure

```python
def function_name(arg1: int, arg2: str) -> int:
    """One-line summary that fits on one line.

    Optional longer description that provides more context about what
    the function does, why it exists, and any important behavioral
    notes. This can span multiple paragraphs if needed.

    Args:
        arg1: Description of arg1. Type should be in type hints, not
            here.
        arg2: Description of arg2. Explain the purpose, not just the
            type.

    Returns:
        Description of the return value. Focus on what it represents.

    Raises:
        ValueError: When arg1 is negative.
        KeyError: When arg2 is not found in the internal mapping.

    Example:
        >>> function_name(5, "key")
        42
    """
```

#### Module-level docstrings

Place a module docstring at the very top of each file (after the
shebang and encoding, if present, but before imports):

```python
"""Brief one-line description of the module.

Longer description explaining the module's purpose, main
classes/functions, and how it fits into the overall package
architecture.
"""

import os
import sys
```

#### Class docstrings

```python
class WeightedVotingEnsembleAggregator:
    """Aggregates responses from multiple LLM machines using weighted
    voting.

    This class implements a talker that queries multiple language
    machines and combines their responses using configurable weights.
    It supports both simple majority voting and confidence-weighted
    aggregation.

    Attributes:
        machines: The sequence of language machines in the ensemble.
        weights: The weight assigned to each model's response.
    """

    def __init__(
        self,
        models: Sequence[LLModel],
        weights: Sequence[float] | None = None,
    ) -> None:
        """Initialize the ensemble aggregator."""
```

**Note:** The `Args:` section in a class docstring describes `__init__`
parameters.

#### Method and function docstrings

```python
def score_response(
    self, thinking_state: Thoughts, response: str
) -> float:
    """Score a model response based on quality metrics.

    Evaluates the response using configured scoring criteria including
    relevance, coherence, and aspect compliance. Returns a normalized
    score between 0.0 and 1.0, where higher values indicate better
    quality.

    Args:
        thinking_state: The input thoughts containing message and
            aspects.
        response: The model-generated response to evaluate.

    Returns:
        Normalized quality score between 0.0 and 1.0.

    Raises:
        ValueError: If thinking_state.message is empty.
        RuntimeError: If the scoring model is not initialized.
    """
```

#### Properties

For `@property` decorated methods, write the docstring as if it's an
attribute:

```python
@property
def is_empty(self) -> bool:
    """True if the dictionary contains no items, False otherwise."""
    return len(self) == 0
```

### Section order

Use sections in this order (omit any that don't apply):

1. Summary (one line)
2. Extended description (optional)
3. `Args:` (for functions/methods)
4. `Attributes:` (for classes)
5. `Returns:` or `Yields:` (for generators)
6. `Raises:`
7. `Example:` or `Examples:` (optional but encouraged for non-obvious usage)
8. `Note:` or `Warning:` (if needed)

### Type hints vs. docstrings

**Use type hints in function signatures** for all parameters and return
values. Do not repeat type information in the docstring:

✅ **Good:**
```python
def add_item(self, key: str, value: int) -> None:
    """Add an item to the dictionary.

    Args:
        key: The unique identifier for the item.
        value: The numeric value to store.
    """
```

❌ **Bad:**
```python
def add_item(self, key: str, value: int) -> None:
    """Add an item to the dictionary.

    Args:
        key (str): The unique identifier for the item.
        value (int): The numeric value to store.
    """
```

If a parameter accepts multiple types or has constraints, explain in
the description:

```python
def set_timeout(self, seconds: float | None) -> None:
    """Set the operation timeout.

    Args:
        seconds: Timeout duration in seconds, or None to disable
            timeout.
    """
```

### Focus on WHAT and WHY

Docstrings should explain:
- **WHAT** the function/class does
- **WHY** it exists or why certain design choices were made
- **HOW** only when the approach is non-obvious

✅ **Good:**
```python
def aggregate_responses(self, responses: list[str]) -> str:
    """Select the best response from multiple LLM outputs.

    Combines responses using weighted voting and semantic similarity
    to choose the most representative answer. This reduces the impact
    of outlier responses and improves overall quality.

    Args:
        responses: List of response strings from different machines.

    Returns:
        The selected best response.
    """
```

❌ **Bad (too focused on HOW):**
```python
def aggregate_responses(self, responses: list[str]) -> str:
    """Select the best response from multiple LLM outputs.

    First computes embeddings for each response, then calculates
    pairwise cosine similarities, builds a similarity matrix, and
    picks the response with the highest average similarity to others.

    Args:
        responses: List of response strings from different machines.

    Returns:
        The selected best response.
    """
```

### Do not use reStructuredText cross-reference roles in docstrings

While reStructuredText (reST) roles like `:class:`, `:meth:`, etc. are
supported by some documentation tools, they:

- Make docstrings harder to read in source code and IDEs
- Create tool dependencies (requiring specific doc generators)
- Can break when class/method names change
- Don't add significant value over clear prose descriptions

Instead, use plain text references and let documentation tools handle
cross-linking.

---

## Comments

Comments should clarify **intent**, **reasoning**, and **non-obvious
behavior**.

Avoid stating the obvious, be precise and concise. Comments should add
value by explaining things that are not immediately clear from the code
itself. If the code is self-explanatory, adding a comment just creates
noise and maintenance overhead. 

### Inline comments

Use inline comments sparingly. Place them on the same line as the code
or on the line immediately above.

✅ **Good (explains WHY):**
```python
# Delay to ensure distinct timestamps on filesystems with 1-second
# granularity
time.sleep(1.1)
```

✅ **Good (explains WHAT in a non-obvious context):**
```python
# UNC paths on Windows require special handling
if path.startswith("\\\\"):
    return self._handle_unc_path(path)
```

❌ **Bad (states the obvious):**
```python
# Increment counter
counter += 1
```

❌ **Bad (explains trivial HOW):**
```python
# Loop through all items
for item in items:
    process(item)
```

### Block comments

Use block comments for explaining complex algorithms, edge cases, or
design decisions:

```python
# LLM APIs may return non-deterministic results even with fixed seeds
# due to infrastructure variations. To ensure reproducible experiments,
# we cache responses keyed by (model, seed, prompt). Cache entries are
# stored per time_scale bucket to support temporal versioning. This
# trades off storage space for deterministic behavior across runs.
if self._should_use_cache(thinking_state):
    response = self._get_cached_response(thinking_state)
    return response
```

### TODOs, FIXMEs, and NOTEs

Use standard tags for annotations:

```python
# TODO: Add support for nested directory structures.
# FIXME: Race condition when multiple processes write simultaneously.
# NOTE: This implementation assumes keys are ASCII strings.
```

Include a GitHub issue reference if applicable:
```python
# TODO(#123): Migrate to the new serialization format.
```

### Comments for non-obvious "HOW"

When implementation is tricky, explain HOW:

```python
def parse_expression(self, tokens: list[str]) -> AST:
    """Parse a mathematical expression into an abstract syntax tree.

    Uses the Shunting Yard algorithm to handle operator precedence
    and associativity rules during the parsing process.
    """
    # Use two stacks to implement Shunting Yard:
    # - operator_stack holds operators waiting to be processed
    # - output_queue builds the AST by combining operands with
    #   operators
    operator_stack = []
    output_queue = []
    ...  # Implementation details
```

### Avoid commented-out code

Don't leave large blocks of commented-out code in the repository. Use
version control to preserve history.

✅ **Good:**
```python
def process_data(self, data: list) -> list:
    return self._new_algorithm(data)
```

❌ **Bad:**
```python
def process_data(self, data: list) -> list:
    # Old approach:
    # result = []
    # for item in data:
    #     result.append(transform(item))
    # return result
    return self._new_algorithm(data)
```

If you must temporarily disable code during development, use a clear
comment explaining why:

```python
# Temporarily disabled while investigating issue #456
# self._validate_integrity()
```

### Avoid using inline commands in comments

Inline commands in comments (like `# pylint: disable=invalid-name` or
`# type: ignore`) should be avoided because they:

1. Make code harder to maintain by hiding configuration in scattered
   comments
2. Create implicit dependencies on specific tools
3. May break when tools are updated or replaced
4. Often indicate underlying code quality issues that should be fixed
   properly

Instead:

- Use configuration files (pyproject.toml, setup.cfg, etc.) for tool
  settings
- Fix the underlying code issues rather than suppressing warnings
- If suppressions are absolutely necessary, document WHY in the comment

---

## Best practices from the Python community

1. **PEP 257 – Docstring Conventions**: All docstrings should be
   triple-quoted (`"""`), even one-liners. One-liners should have both
   quotes on the same line:
   ```python
   def get_name(self) -> str:
       """Return the name of this instance."""
   ```

2. **PEP 8 – Comments**: Comments should be complete sentences. The
   first word should be capitalized unless it's an identifier that
   begins with a lowercase letter.

3. **PEP 20 – The Zen of Python**: "Explicit is better than implicit."
   Write comments and docstrings that make your intentions clear.

4. **Consistency**: Match the style of existing code in the module. If
   the surrounding code uses certain phrasing or structure, follow it.

5. **Readability counts**: Prefer clarity over cleverness. If you need
   a comment to explain code, consider refactoring the code to be more
   self-explanatory first.

---

## Examples: Good vs. Bad

### Example 1: Function docstring

❌ **Bad:**
```python
def combine(responses, weights):
    # This function combines responses
    return weighted_average(responses, weights)
```

✅ **Good:**
```python
def combine_model_responses(
    responses: list[str], weights: list[float]
) -> str:
    """Combine multiple model responses using weighted selection.

    Selects the response with the highest weighted score based on
    model confidence and historical performance. This approach balances
    between trusting high-performing machines and maintaining ensemble
    diversity.

    Args:
        responses: List of response strings from different machines.
        weights: Confidence weights for each model, summing to 1.0.

    Returns:
        The selected response string.
    """
    ...  # Implementation omitted; focus on WHAT/WHY in the docstring
```

### Example 2: Inline comment

❌ **Bad:**
```python
score = base_score + 0.1  # Add 0.1 to base_score
```

✅ **Good:**
```python
# Boost score for responses that include citations
score = base_score + CITATION_BONUS
```

### Example 3: Class with complex behavior

✅ **Good:**
```python
class CachedModelWrapper:
    """Wraps an LLM with response caching for deterministic behavior.

    This class ensures reproducible results by caching model responses
    keyed by (prompt, seed, rounded_timestamp, storage). Cached
    responses are returned for identical inputs, eliminating API
    non-determinism.

    Attributes:
        model: The underlying LLModel to wrap with caching
            functionality.
        rounded_timestamp: Optional time-based cache bucketing.
            If None, caching is done without time consideration.
        seed: Optional seed value for deterministic response generation.
            If None, the model's default behavior is used.
        storage: Optional storage backend for caching responses.
            If None, an in-memory cache is used.

    Raises:
        ValueError: If time_scale is provided without timestamp support.

    Example:
        >>> model = CachedModelWrapper(base_model)
        >>> resp1 = model.respond("Hello")  # Calls API
        >>> resp2 = model.respond("Hello")  # Returns cached
        >>> assert resp1 == resp2  # Guaranteed equal
    """
```

---

## LLM-Friendly Docstring and Comment Patterns

This section provides guidance for writing docstrings and comments that
remain stable and maintainable when AI/LLM agents generate or modify
code.

### Design for Stability Under AI Changes

**Use consistent docstring structure:**
- Always follow the same section order (Summary, Args, Returns, Raises,
  Example)

**Prefer semantic descriptions over implementation details:**
- When implementation changes, semantic descriptions remain valid
- AI agents can update implementation without invalidating docstrings

**Keep parameter descriptions focused on purpose:**
- ✅ Good: `timeout: Maximum wait time; None disables timeout`
- ❌ Fragile: `timeout: Passed to socket.settimeout() after conversion`
- Purpose-focused descriptions survive refactoring better
- LLMs can infer implementation from type hints and purpose

**Avoid brittle cross-references:**
- ✅ Good: "Returns a list of validated items, similar to standard
  filtering"
- ❌ Fragile: "Returns same format as UtilsModule.validate_all() in
  utils/helpers.py:142"
- Explicit file/line references break when code moves
- AI refactoring tools can relocate code without breaking docstrings

**Use standard terminology consistently:**
- Follow the project glossary defined in [GLOSSARY.md](https://github.com/pythagoras-dev/pythagoras/blob/master/GLOSSARY.md)
  (e.g., "machine" for LLM instances, "portal" for controlled execution
  contexts)
- Consistent terms improve AI-generated code quality and reduce
  ambiguity
- Makes automated documentation generation more coherent
- When introducing new project-wide architectural or domain concepts,
  add them to [GLOSSARY.md](https://github.com/pythagoras-dev/pythagoras/blob/master/GLOSSARY.md) in a logical order that builds
  on existing terms. Avoid adding module-specific or trivial terms that
  create cognitive overload

### Token and Complexity Considerations

**Keep docstrings concise but complete:**
- Aim for <4-7 lines for typical functions, <10-15 for complex ones
- Very long docstrings (>30 lines) bloat context windows for AI agents
- Break down functions if docstrings become too long
- Use `Example:` section only when behavior is non-obvious

**Avoid excessive examples in docstrings:**
- ✅ Good: 1-2 focused examples showing typical usage
- ❌ Problematic: 10+ examples covering every edge case
- Put comprehensive examples in separate test files or docs
- AI agents can discover edge cases from tests, not docstrings

**Use descriptive parameter names to reduce documentation needs:**
- `max_retries` is better than `n` (reduces docstring explanation)
- `include_metadata: bool` is clearer than `meta: bool`
- Good names make docstrings shorter and clearer for LLMs
- AI code generation tools rely heavily on parameter names

**Structure complex behavior with clear subsections:**
```python
def complex_operation(data: dict) -> Result:
    """Process data through multi-stage pipeline.

    Stages:
    1. Validation: Checks schema and constraints
    2. Transformation: Applies configured transforms
    3. Aggregation: Combines results using strategy pattern

    Args:
        data: Input dictionary with keys: schema, records, config

    Returns:
        Processed result with validation_errors and output fields
    """
```
- Numbered/bulleted structure helps LLMs parse logic
- Clear stage separation aids AI-powered refactoring
- Structured docs are easier to update programmatically

### AI-Maintainable Comment Patterns

**Prefer self-documenting code over comments:**
```python
# ❌ Fragile (comment explains bad code):
# Get the sum of all positive numbers
s = sum([x for x in nums if x > 0])

# ✅ Better (code explains itself):
positive_sum = sum(x for x in nums if x > 0)

# ✅ Best (extracted function, no comment needed):
def sum_positive_numbers(nums: list[int]) -> int:
    """Return the sum of all positive numbers in the list."""
    return sum(x for x in nums if x > 0)
```
- Self-documenting code survives AI refactoring better
- LLMs are less likely to update comments when changing code
- Extract functions instead of adding inline comments

**Use intention-revealing variable names:**
```python
# ❌ Fragile:
# Retry delay in seconds
t = 1.5

# ✅ Stable:
retry_delay_seconds = 1.5
```
- Descriptive names eliminate a need for many comments
- AI agents better understand and modify well-named variables
- Reduces maintenance burden across refactorings

**Document WHY, not WHAT, for complex logic:**
```python
# ✅ Good (explains rationale):
# Use exponential backoff to avoid overwhelming the API during outages
for attempt in range(max_retries):
    delay = base_delay * (2 ** attempt)
    time.sleep(delay)

# ❌ Fragile (explains obvious mechanics):
# Multiply base_delay by 2 to the power of attempt
for attempt in range(max_retries):
    delay = base_delay * (2 ** attempt)
    time.sleep(delay)
```
- WHY-focused comments remain valid across implementation changes
- AI agents preserve intent-comments better than mechanics-comments
- Rationale helps LLMs make informed refactoring decisions

**Use TODO comments with clear, actionable descriptions:**
```python
# ✅ Good (actionable, specific):
# TODO(#456): Replace with async implementation once we upgrade to
# Python 3.11+ for better task group support

# ❌ Fragile (vague, no context):
# TODO: make this better
```
- Specific TODOs help AI agents understand constraints
- Issue references provide context for automated cleanup tools
- Clear descriptions enable AI-assisted TODO resolution

---

## Summary

- **Always use Google-style docstrings** for public APIs.
- **Explain WHAT and WHY**, not HOW (unless non-obvious).
- **Write comments that add value**, not noise. Be precise and concise.
  Don't duplicate type-hints in docstrings
- **Be consistent** with the existing codebase.
