# EVAL_MANIFEST — formato e semântica de congelamento

`eval_manifest.yaml` vive junto à skill candidata sendo construída (não
dentro de `rech-skill-creator/`) — é um input do pipeline, não um artefato
da própria skill-creator.

## Formato

```yaml
manifest_version: 1
skill_under_test: "<skill_id>"
skill_version: "<string | 'candidate'>"

evals:
  - eval_id: "EVAL-RSC-001"
    description: "<...>"
    category: "trigger" | "near_miss" | "functional" | "regression" | "adversarial"
    execution_mode: "cli_subprocess" | "claude_invocation" | "manual_required"
    input:
      cmd: ["<argv0>", "<arg1>", ...]   # obrigatório para cli_subprocess
    assertions:
      - type: "exit_code" | "contains" | "regex" | "exact"
        target: "stdout" | "stderr"      # default stdout
        expected: "<literal ou padrão>"
    primary: true|false      # exatamente um true por manifesto; nunca inferido por posição
    baseline_ref: "ORIGINAL" | "PREVIOUS" | "<tag de versão explícita>"   # nunca por ordem
    required: true|false     # default true — VALID_RUN_GATE exige presença em toda run
    timeout_seconds: 60

metadata:
  created_by: "<...>"
  created_at: "<ISO8601>"
```

Um "eval declarado" = uma entrada de `evals[]` completa (id + description +
input + assertions + `required`). `execution_mode: claude_invocation` ou
`manual_required` são valores de primeira classe: `run_executor.py` os
classifica honestamente como `RUN_INVALID` (não pode executar isso neste
harness offline) em vez de pular silenciosamente.

## Congelamento (`snapshot_manager.py`)

1. `yaml.safe_load()` do manifesto de trabalho.
2. Recanonicalização determinística (`yaml.safe_dump(sort_keys=True,
   default_flow_style=False)`) — edições puramente cosméticas nunca mudam o
   hash resultante; qualquer mudança de valor real sempre muda.
3. `manifest_sha256 = sha256(bytes canônicos)`.
4. Cópia canônica gravada em `snapshot/eval_manifest.canonical.yaml`. **Todo
   estágio downstream (`run_executor.py`, `valid_run_gate.py`) só pode abrir
   essa cópia** — nunca o arquivo de trabalho ao vivo. Isso é o mecanismo
   estrutural que impede uma run de enxergar um manifesto que não foi
   congelado antes (defeitos #1/#8).
5. Um `assertions_digest` por eval também é calculado, para relatórios
   futuros poderem nomear exatamente qual eval mudou, não só "o manifesto".

"Este snapshot corresponde a este conjunto exato de manifesto+runs" é
respondido por: todo `run-N/run_meta.json` grava o `manifest_sha256` (e o
`manifest_id`, hash sobre todos os decision inputs) contra o qual rodou;
`valid_run_gate.py` não avalia uma run cujo `manifest_sha256` gravado não
bata com a cópia congelada atual em disco.
