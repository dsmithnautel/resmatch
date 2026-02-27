# Hybrid Rendering: LLM Initial + Deterministic Edits

## Problem

Every bullet edit on the compare page triggers a full LLM round-trip (~10-20s) just to regenerate the entire LaTeX document. This is wasteful since only one bullet changed.

## Solution

Use the LLM **only once** during the initial compile to produce high-quality LaTeX. On the compare page, when a user edits a bullet, do a direct string replacement in the stored LaTeX and recompile with Tectonic (~130ms).

## Changes

### 1. New backend endpoint: `POST /resume/patch-latex`

Add to `backend/app/routers/resume.py`.

- Accepts `{ latex: string, patches: [{ old_text: string, new_text: string }] }`
- For each patch, does a LaTeX-safe string replacement in the stored LaTeX source (escaping special LaTeX characters in the new text)
- Compiles the patched LaTeX with Tectonic
- Returns PDF bytes
- Pure string operation + Tectonic — no LLM, ~130ms total

### 2. New utility: LaTeX-safe escaping for patch text

Add a helper (can live in `renderer.py` or a shared util) that escapes `& % $ # _ { } ~ ^ \` in user-edited text before patching into the LaTeX source. The old text from the LLM-generated LaTeX is already escaped, so the replacement target should match what's in the `.tex`.

### 3. Frontend API function: `patchLatex`

Add to `frontend/lib/api.ts`:

```typescript
export async function patchLatex(
  latex: string,
  patches: { old_text: string; new_text: string }[]
): Promise<Blob>
```

Calls `POST /resume/patch-latex`, returns a PDF `Blob`.

### 4. Frontend: track original tailored text per bullet

In the compare page (`frontend/app/compare/[compileId]/page.tsx`):

- Store the original LLM-tailored text for each bullet alongside the current edited text
- When the debounce fires after an edit, compute diffs: which bullets changed from their original tailored text
- Build the `patches` array: `{ old_text: original, new_text: edited }` for each changed bullet

### 5. Frontend: swap `generatePdf` to use `patchLatex` when LaTeX is available

- If `compileResult.tailored_latex` exists (it will after the LLM compile), use `patchLatex` for edits instead of calling `/preview`
- Fall back to `/preview` (LLM) only if no stored LaTeX exists
- Initial page load still uses `compileLatex` (just Tectonic on stored LaTeX) — no change

### 6. Keep `/preview` as LLM fallback

No changes to the preview endpoint — it stays as the LLM-based fallback for cases where stored LaTeX isn't available.

## Flow After Implementation

| Step | Method | Latency |
|------|--------|---------|
| Initial compile | Gemini generates LaTeX → Tectonic compiles → stored in DB | ~15-25s (once) |
| Compare page load | Tectonic recompiles stored LaTeX → PDF | ~130ms |
| Bullet edit | String replace in LaTeX + Tectonic recompile → PDF | ~130ms |
| Recalculate Relevance Scores | Gemini scores only (no LaTeX regen) | ~5s |
