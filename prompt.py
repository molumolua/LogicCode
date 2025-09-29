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
  - O(n log n): often `n ≤ 1e5–5e5`.
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

### Numeric literal
- **All numeric values** you place in `default_scale`, `small_scales`, and `large_scales` **must be Python/JSON-parseable numeric literals**:
  - Allowed: integers like `1000000`; floats like `0.001`; scientific notation like `1e6` or `2.5e-3`.
- Ensure **every value is a number type** (int or float) — **not** a string.
- within INT32 range (±2e9) if possible; otherwise, INT64 (±9e18).
- When these numbers appear in the rendered `template`, they should appear exactly as inserted (e.g., `1e6` or `1000000`), with no extra formatting.


### Output format (must follow exactly)
- Return **one** Python code block with:
  - Module docstring explaining what was interpreted as “data scale”.
  - The three required top-level variables: `template`, `default_scale`, `small_scales`, `large_scales`.
  - Brief inline comments justifying the chosen small/large tiers by complexity bands (e.g., “tier 1 supports O(n³) brute force because n≤300”, etc.).

### Edge cases
- If the prompt has **multiple inputs** (e.g., arrays per test case), introduce placeholders for each relevant bound (`{{n_max}}`, `{{q_max}}`, `{{ai_max}}`, …).
- If the original mixes absolute limits and typical values, set defaults to **exactly** the original absolute limits.

### Final reminder
- Your code must be immediately usable as:
```python
text = template.format(**default_scale)
# and similarly for any dict in small_scales / large_scales
```
- Lists small_scales and large_scales must each have length ≤ 3.

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

generator_cmd_prompt= '''
You are given the following input:

1. A C++ code, which is compiled into an executable file `./gen`. This code generates test cases for a competitive programming problem.
2. A JSON object configuration, which outlines the problem's data size constraints. This configuration may reflect limits and conditions that are mentioned in the problem description.
3. The data size constraints are crucial because they control the time complexity necessary to solve the problem, thus influencing the difficulty level. I will provide you with a list of JSON configurations, each corresponding to a different data size, arranged from smallest to largest.

Your task is to generate a series of commands. These commands will execute the `./gen` file and will be wrapped in ```bash``` tags. Specifically, you must organize the commands into groups:

- Each group should contain **20 commands** with different CLI arguments, and each group corresponds to a configuration in the list, sorted in ascending order of data size.
- For example:
    - When testing with the smallest configuration, the first **20 commands** should be generated.
    - For the second configuration (slightly larger), generate **40 commands** (first 40 commands in sequence).
    - For the third configuration, generate **60 commands**, and so on, ensuring that the groups grow in size according to the increasing configurations.
- Insert **one single-line comment** between consecutive groups as a separator (e.g., `# ----- Group k: <brief note> -----`).
- For every command, ensure it differs from others in its **CLI arguments** so we get diverse test cases within and across groups.

**Key Requirements:**
1. **Data Coverage for Edge Cases**: Regardless of which data size I select, ensure that the commands **cover all possible edge cases** for the problem. The commands should stress test the problem's limits and check the **maximum values** for each configuration.
2. The data size of CLI arguments should be arranged from smallest to largest. 
3. The commands should allow me to test across different levels of problem difficulty, ensuring that each configuration produces the necessary data to assess the problem's complexity and behavior across a range of sizes.
4. **Group Separation**: Each group of commands should be separated by a **single-line comment** to clearly distinguish between different groups.

**Output Format:**
```bash
# ----- Group 1: <note> -----
./gen <args_for_cmd_1>
...
./gen <args_for_cmd_20>
# ----- Group 2: <note> -----
./gen <args_for_cmd_21>
...
./gen <args_for_cmd_60>
...
```

Now, read the provided C++ generator program, the JSON object configuration,the list of JSON configurations of different data sizes and output the corresponding bash commands in ```bash ```.

** C++ generator program:**
```cpp
{case_code}
```
** JSON object configuration:**
```json
{default_scale}
```
** List of JSON configurations of different data sizes:**
```json
{scale_list}
```
'''

generator_40cmd_prompt = """
You are given a *single* C++ source file that uses **testlib** and has already been compiled to an executable `./gen`. That program generates test cases for a competitive programming problem.

Your job: **emit exactly forty (40) shell commands** that each run `./gen` with thoughtfully chosen CLI arguments so that the resulting 40 test files together provide broad, rigorous coverage:
- edge cases (minimums, zeros, degenerate structures),
- typical cases,
- adversarial and pathological cases,
- **stress tests hitting configured maxima**,
- and diverse distributions/structures implied by the generator.

### What you must read & infer from the code
1. **Parse CLI options** by scanning for `opt<T>("name", ...)`, default values, enums/strings (e.g., `type`), and any derived constraints (caps, clamping, assertions).
2. **Respect hard limits** found in code (e.g., `n = min(n, 2e5)`, `m = min(m, n*(n-1)/2)`, `assert(1 <= n && n <= 2e5)`, etc.). Never exceed them.
3. Note any **coupled constraints** (e.g., `m` depends on `n`, connectivity flags, component counts, value ranges, parity constraints, sortedness flags).

### Coverage plan (use as a checklist)
Design the 40 commands to collectively cover the following categories (tailor names to the actual flags in the code):
- **Min/degenerate**: smallest valid `n`, `m`, counts = 0/1, empty/singleton structures.
- **Small structured**: lines/paths, stars, cliques, grids, simple cycles, trees, bipartite, etc. (if supported by `type` or toggles).
- **Medium random**: moderate sizes with uniform or skewed distributions; different `type`/mode values.
- **Corner-value ranges**: min/max for weights/values/coordinates, negative/zero/positive if allowed; duplicates/ties; sortedness on/off.
- **Adversarial**: worst-case shapes for common algorithms (e.g., long chains, high diameter, many components, near-dense graphs, heavy duplicate keys), respecting constraints.
- **Parameter cross-product**: combine flags that interact (e.g., `connected=0/1`, `distinct=0/1`, `directed=0/1`, `weighted=0/1`, etc.).
- **Boundary-near**: just below/at maxima (e.g., `n = n_max-1`, `n = n_max`; `m` near caps).
- **Stress maxima**: hit maximum feasible sizes allowed by the code and constraints.
- **Invalid-guarded fronts**: if the generator internally clamps or rejects, choose values that *exercise* those branches while still producing valid output.

### Output requirements (strict)
- **Output exactly 40 commands**.
- **Wrap them in a single fenced code block labeled `bash`**.
- Each line must be a command that starts with `./gen` followed only by **valid CLI flags that the code supports** (e.g., `-n`, `-m`, `-type`, `-seed`, and any others discovered).
- **No extra commentary, no blank lines, no redirections**, no `mkdir`, no `echo`, no shebangs—**just the 40 `./gen ...` lines**.
- Do **not** invent flags; only use those present in the code.
- **Respect all assertions and clamping logic**; never request an infeasible parameter combination.

### IMPORTANT
Return **only** one fenced code block:
```bash
./gen -flag1 ...
...
(40 lines total)

** C++ generator program:**
```cpp
{case_code}
```
"""

if __name__ == "__main__":
    # example usage
    case_code = "print(42)"
    problem = "what your name?"
    print(upgrade_prompt.format(code=case_code))
    print(extract_number_prompt.format(problem=problem))
