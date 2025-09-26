# 可直接调用：print(generator_code.format(**default_scale))
generator_code = """#include "testlib.h"
#include <bits/stdc++.h>
using namespace std;

int main(int argc, char* argv[]) {{

registerGen(argc, argv, 1);

int n = opt<int>("n");
int m = opt<int>("m");
string type = opt<string>("type", "random");

// Enforce constraints on m
m = min(m, n * (n - 1) / 2);
m = min(m, {m_cap});

vector<pair<int,int>> edges;

if (type == "random") {{
// Generate m random edges
set<pair<int,int>> edge_set;
while ((int)edge_set.size() < m) {{
int u = rnd.next(1, n);
int v = rnd.next(1, n);
if (u == v) continue;
int x = min(u, v);
int y = max(u, v);
pair<int,int> p = make_pair(x, y);
if (edge_set.count(p) == 0) {{
edge_set.insert(p);
}}
}}
for (auto p : edge_set) {{
edges.emplace_back(p.first, p.second);
}}
}} else if (type == "chain") {{
// Create a chain
if (n - 1 > m) m = n - 1; // Minimum edges for a chain
for (int i = 1; i < n; ++i) {{
edges.emplace_back(i, i+1);
}}
// Fill the rest with random edges if needed
set<pair<int,int>> edge_set(edges.begin(), edges.end());
while ((int)edges.size() < m) {{
int u = rnd.next(1, n);
int v = rnd.next(1, n);
if (u == v) continue;
int x = min(u, v);
int y = max(u, v);
pair<int,int> p = make_pair(x, y);
if (edge_set.count(p) == 0) {{
edge_set.insert(p);
edges.emplace_back(x, y);
}}
}}
}} else if (type == "star") {{
// Create a star graph
int center = 1; // Can be any node
for (int i = 1; i <= n; ++i) {{
if (i != center) {{
edges.emplace_back(center, i);
if ((int)edges.size() == m) break;
}}
}}
// Fill the rest with random edges if needed
set<pair<int,int>> edge_set(edges.begin(), edges.end());
while ((int)edges.size() < m) {{
int u = rnd.next(1, n);
int v = rnd.next(1, n);
if (u == v) continue;
int x = min(u, v);
int y = max(u, v);
pair<int,int> p = make_pair(x, y);
if (edge_set.count(p) == 0) {{
edge_set.insert(p);
edges.emplace_back(x, y);
}}
}}
}} else if (type == "complete") {{
// Create a complete graph
for (int u = 1; u <= n; ++u) {{
for (int v = u+1; v <= n; ++v) {{
edges.emplace_back(u, v);
if ((int)edges.size() == m) break;
}}
if ((int)edges.size() == m) break;
}}
}} else if (type == "sparse") {{
// Create a sparse graph (a tree plus some random edges)
int min_edges = min(m, n - 1);
// Build a spanning tree
for (int i = 2; i <= min(n, min_edges + 1); ++i) {{
int u = rnd.next(1, i - 1);
edges.emplace_back(u, i);
}}
// Fill the rest with random edges if needed
set<pair<int,int>> edge_set(edges.begin(), edges.end());
while ((int)edges.size() < m) {{
int u = rnd.next(1, n);
int v = rnd.next(1, n);
if (u == v) continue;
int x = min(u, v);
int y = max(u, v);
pair<int,int> p = make_pair(x, y);
if (edge_set.count(p) == 0) {{
edge_set.insert(p);
edges.emplace_back(x, y);
}}
}}
}} else if (type == "dense") {{
// Create a dense graph
for (int u = 1; u <= n; ++u) {{
for (int v = u+1; v <= n; ++v) {{
edges.emplace_back(u, v);
if ((int)edges.size() == m) break;
}}
if ((int)edges.size() == m) break;
}}
}} else {{
cerr << "Unknown type: " << type << endl;
return 1;
}}

// Randomly assign directions and shuffle edges
for (auto& e : edges) {{
if (rnd.next(2)) {{
swap(e.first, e.second);
}}
}}

shuffle(edges.begin(), edges.end());

// Output the test case
printf("%d %d\\n", n, (int)edges.size());
for (auto& e : edges) {{
printf("%d %d\\n", e.first, e.second);
}}

return 0;

}}
"""

# 你给的默认参数；注意其中 n_max 在这份代码里未被使用是允许的
default_scale = {
    "n_max": 5000,
    "m_cap": 5000,
}


print(generator_code.format(**default_scale))

# 使用示例（会还原出你原始的 C++ 代码文本，m 的上限为 5000）：
# restored_cpp = generator_code.format(**default_scale)
# print(restored_cpp)
