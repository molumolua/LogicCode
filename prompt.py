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

if __name__ == "__main__":
    # example usage
    case_code = "print(42)"
    print(upgrade_prompt.format(code=case_code))
