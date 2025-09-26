case_code='''
#include <bits/stdc++.h>
using namespace std;
int t,n,a[10010];
int maxx;
int main(){
	scanf("%d",&t);
	while(t--){
		scanf("%d",&n);
		maxx=-1;
		int cnt=0;
		for(int i=1;i<=n;i++) scanf("%d",&a[i]),maxx=max(maxx,a[i]);
		for(int i=1;i<=n;i++) if(a[i]==maxx) cnt++;
		if(cnt==n) printf("-1\n");
		else{
			printf("%d %d\n",n-cnt,cnt);
			for(int i=1;i<=n;i++) if(a[i]!=maxx) printf("%d ",a[i]);printf("\n");
			for(int i=1;i<=n;i++) if(a[i]==maxx) printf("%d ",a[i]);printf("\n");
		}
	}
	return 0;
} 
'''


# English prompt (coherent, marker-free)
upgrade_prompt = (
    "You are given a code listing originally written for a programming contest.\n"
    "Your job is to: (1) analyze the techniques/algorithms used; and (2) upgrade "
    "EXACTLY ONE logically contiguous part of the program to a strictly stronger "
    "technique/algorithm.\n\n"
    "Important scope clarifications:\n"
    "- The upgraded code is NOT intended to solve the same problem as the original.\n"
    "- Do NOT consider practical meaning; the program only needs to compute and print a single numeric value.\n"
    "- Make a SINGLE-PART edit (e.g., replace one function, one loop-nest, or one data-structure block). "
    "Avoid full rewrites or multi-part refactors.\n\n"
    "Upgrade guidelines:\n"
    "- “Stronger” means asymptotically faster OR theoretically more powerful/general (e.g., naive convolution → FFT/NTT/FWHT; "
    "O(n^2) DP → convex-hull trick/Divide & Conquer DP; brute-force subset ops → SOS DP/bitset; naive counts → prefix-sums/Fenwick/segment tree; "
    "naive string ops → suffix array/automaton; graph scans → HLD/LCT/Mo’s algorithm/CDQ divide-and-conquer; etc.).\n"
    "- Keep the language the same as the original; if uncertain, default to Python. Use only the standard library. "
    "Keep the program self-contained and runnable.\n"
    "- The final program must simply print one numeric value (any value you compute), regardless of the original semantics.\n\n"
    "Runtime & correctness constraints:\n"
    "- Prioritize correctness. Handle basic edge cases and avoid undefined behavior.\n"
    "- Ensure the program finishes within ~1 second on typical inputs. If needed, conservatively cap loop bounds, clamp input sizes, "
    "or choose smaller yet representative parameters—while still demonstrating the stronger technique.\n"
    "- No external dependencies, and no nondeterministic randomness. Use only stdin/stdout for I/O.\n\n"
    "Original Code:\n"
    "<BEGIN CODE>\n"
    "{code}\n"
    "<END CODE>\n\n"
    "Return ONLY the sections specified below.\n\n"
    "=== REQUIRED OUTPUT FORMAT ===\n"
    "### Analysis\n"
    "- Detected technique(s): <list>\n"
    "- Estimated complexity (original): <e.g., O(n log n)>\n"
    "- Upgrade idea (single-part): <one sentence on the stronger method and why>\n\n"
    "### Upgraded Code (single-part edit)\n"
    "```<language>\n"
    "<Full program reproduced with EXACTLY ONE modified block; do NOT include any edit markers or tags.>\n"
    "```\n"
)

extract_number_prompt = '''
**Role:** You are a precise extractor of input-size constraints from programming problem statements, and a generator of Python scaffolding that parameterizes those constraints for curriculum-style scaling.

**User Input:** The input section in a single programming problem statement for a *code generation* task (e.g., typical competitive programming prompt).

**Your Task:** Read the statement and output **only one Python script** (as a single code block) that defines:
1. `template: str` — the original input section of the problem statement as a Python f-string *or* `.format()` template where **all input-size figures/limits** (e.g., `n`, `m`, `q`, number of test cases, value ranges, time limits if relevant to scale) are replaced by named placeholders like `{{n}}`, `{{m}}`, `{{q}}`, `{{t}}`, `{{max_ai}}`, etc.
2. `default_scale: dict` — a dictionary of concrete values for every placeholder so that `template.format(**default_scale)` **reconstructs the input section of the original statement verbatim** (same numbers/limits and wording).
3. `small_scales: list[dict]` — up to **3** dictionaries. Each must be directly usable as `template.format(**scale)` and must set **strictly smaller** input sizes than `default_scale`. They must be chosen so that the resulting instances can be solved by **progressively *higher* time-complexity** algorithms (e.g., O(n) → O(n log n) → O(n²) → O(n³) → …). Order them from **hardest (closest to default) **  to **easiest (smallest)**  within the “small” regime. The easiest tier should be solvable by the most naive/brute-force method.
4. `large_scales: list[dict]` — up to **3** dictionaries. Each must be directly usable as `template.format(**scale)` and must set **strictly larger** input sizes than `default_scale`. They must be chosen so that the resulting instances require **progressively *lower* time-complexity** algorithms (e.g., O(n log n) → O(n) → near-linear / sublinear). Order them from **easiest (closest to default)** to **hardest (largest)**. The hardest tier should be solvable by the most efficient algorithms or within the constant time.

> The three objects must be self-consistent: every placeholder in `template` appears as a key in `default_scale`, and in every dict in both lists.

### Complexity-aware scaling rules (follow strictly)
- Map common algorithmic families to typical safe input sizes (guideline, adjust to domain):
  - O(n³): up to ~2e3 ops, often `n ≤ 150–300`.
  - O(n²): up to ~1e7 ops, often `n ≤ 3e3–1e4`.
  - O(n log n): up to ~1e7–1e8 ops, often `n ≤ 1e5–5e5`.
  - O(n): up to ~1e8 ops, often `n ≤ 1e6–1e7`.
  - O(m log n) graphs: `n ≤ 2e5`, `m ≤ 2e5–5e5`.
  - O(n√n) (e.g., Mo’s): `n ≤ 2e5` with careful constants.
  - O(2^n): keep total ops ≲ ~1e6–1e7; typical `n ≤ 20–24` depending on constants/pruning.
- Different scales must correspond to **distinct complexity bands** (e.g., O(n²) vs. O(n log n)), not just small constant-factor changes.
- If the problem has **multiple drivers** (e.g., `n` and `q`, or `n` and `m`), scale them **together** to control total work (e.g., `n*q`, `m log n`, `n*k`, etc.).
- Respect **value ranges** (e.g., `ai ≤ 1e9`) unless they are purely content, not scale. Do not change semantic constants (like modulus 1e9+7).
- If the original has **multiple test cases `t`**, keep `t` as a placeholder and scale it too. Ensure total work `t * per_case_work` aligns with the intended complexity tier.

### Extraction & templating guidelines
- Convert explicit constraints like “`2 ≤ n ≤ 2e5`” into `{{n_max}}` and keep phrasing intact, e.g., “`2 ≤ n ≤ {{n_max}}`”.
- If the statement gives only examples (no constraints), infer sensible `*_max` from context and typical CP norms, and **document your inference in code comments**.
- Keep all non-scale text identical to the original; only replace scale numbers/limits with placeholders.
- Use **descriptive placeholder names**: `{{n}}`, `{{m}}`, `{{q}}`, `{{t}}`, `{{n_max}}`, `{{m_max}}`, `{{q_max}}`, `{{ai_max}}`, `{{weight_max}}`, etc.
- Prefer `.format(**dict)`-style formatting (not f-strings) to match the exact requirement.

### Output format (must follow exactly)
- Return **one** Python code block with:
  - Module docstring explaining what was interpreted as “data scale”.
  - The three required top-level variables: `template`, `default_scale`, `small_scales`, `large_scales`.
  - Brief inline comments justifying the chosen small/large tiers by complexity bands (e.g., “tier 1 supports O(n²) brute force because n≤300”, etc.).
  - A tiny self-check at the bottom that asserts `template.format(**default_scale)` is a `str` (don’t print).
- **Do not** include any extra prose outside the code block. **No prints, no execution, no external imports.**

### Edge cases
- If the prompt has **multiple inputs** (e.g., arrays per test case), introduce placeholders for each relevant bound (`{{n_max}}`, `{{q_max}}`, `{{ai_max}}`, …).
- If the original mixes absolute limits and typical values, set defaults to **exactly** the original absolute limits.
- If time/memory limits meaningfully correspond to scale, keep them as placeholders too (e.g., `{{time_limit_sec}}`, `{{memory_limit_mb}}`) and scale only if the statement ties algorithm choice to them; otherwise keep as constants.

### Final reminder
- Your code must be immediately usable as:
  ```python
  text = template.format(**default_scale)
  # and similarly for any dict in small_scales / large_scales
Lists small_scales and large_scales must each have length ≤ 3.

Every dict in those lists must be complete (all placeholders provided).

Now read the input section of the problem statement below and produce the single Python file as specified.

**Input Section:**
{problem}

'''


extract_generator_prompt = '''
You are given as input a single C++ source file that implements a *problem-generator* for an algorithmic contest. Your job is to **emit one Python code block** that parameterizes key numeric constants in that C++ code and allows reconstructing the original code via `.format(**default_scale)`.

## Input
- A raw C++ generator program (as plain text).
- A raw Python dictionary `default_scale` that maps placeholder names to their original numeric values in the C++ code.

## Output (emit exactly one Python code block):
Produce Python code that defines **only** the following objects (and optional helper comments).

`generator_code: str`
   - A **Python format template string** (not a function) that contains the entire original C++ source.
   - Replace only the relevant **hard-coded numeric constants** that are *problem-size caps / default bounds* with named placeholders using Python `.format` syntax, e.g. `{{n_max}}`, `{{m_cap}}`.
   - Keep **all other text, spacing, and newlines identical** to the original C++ (so that formatting reproduces it byte-for-byte).
   - If the C++ contains multiple occurrences of the same cap intended to be the *same semantic cap*, use the **same placeholder name** for all those occurrences.
   - Replace only when the constant is correspond to one of the items in `default_scale`.
   
## Strict requirements
generator_code must be a string template, not a function. It must be usable as:

```python
  restored = generator_code.format(**default_scale)
```
and restored must be byte-identical to the original input C++.

Now, read the provided C++ generator program, the python dictionary `default_scale` and output the single Python code block accordingly.

**C++ generator program:**
```cpp
{case_code}
```

**default_scale dictionary:**
```python
{default_scale}
```
'''


extract_validator_prompt = '''
You are given as input a single C++ source file that implements a *validator / input checker* for an algorithmic contest problem (e.g., based on testlib or a custom parser). Your job is to **emit one Python code block** that parameterizes key numeric constraints in that C++ code and allows reconstructing the original code via `.format(**default_scale)`.

## Input
- A raw C++ validator program (as plain text).
- A raw Python dictionary `default_scale` that maps placeholder names to the original numeric values in the C++ code.

## Output (emit exactly one Python code block):
Produce Python code that defines **only** the following objects (and optional helper comments).

`validator_code: str`
  - A **Python format template string** (not a function) that contains the entire original C++ source **verbatim**.
  - Replace only the relevant **hard-coded numeric constants** that define input constraints / bounds / caps with named placeholders using Python `.format` syntax, e.g. `{{n_min}}`, `{{n_max}}`, `{{m_cap}}`, etc.
  - Typical constants to parameterize include: ranges in `readInt` / `readLong` / `readString` (min/max), array sizes, graph size caps (`n`, `m`), degree limits, value bounds for elements, string length limits, coordinate bounds, alphabet sizes, and any duplicated occurrences of the same semantic limit (including in error messages) that should stay synchronized.
  - Keep **all other text, spacing, and newlines identical** to the original C++ (so that formatting reproduces it byte-for-byte).
  - If the C++ contains multiple occurrences of the same *semantic constraint*, use the **same placeholder name** for all those occurrences.

## Strict requirements
validator_code must be a string template, not a function. It must be usable as:

```python
  restored = validator_code.format(**default_scale)
```
and restored must be byte-identical to the original input C++.

Now, read the provided C++ validator program, the python dictionary `default_scale` and output the single Python code block accordingly.

**C++ validator program:**
```cpp
{case_code}
```

**default_scale dictionary:**
```python
{default_scale}
```
'''


if __name__ == "__main__":
    # example usage
    case_code = "print(42)"
    problem = "what your name?"
    print(upgrade_prompt.format(code=case_code))
    print(extract_number_prompt.format(problem=problem))
