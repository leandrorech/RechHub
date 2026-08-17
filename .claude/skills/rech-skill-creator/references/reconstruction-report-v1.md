# RECH-SKILL-CREATOR RECONSTRUCTION REPORT

Data: reconstrução completa nesta sessão, branch `feat/rech-skill-creator-v1`
recriada a partir da `main` atual do RechHub (que já contém as 5 skills
travadas). Nenhum arquivo fora de `.claude/skills/rech-skill-creator/` foi
tocado — confirmado via `git diff main --stat`.

## A. Files created

33 arquivos, todos sob `.claude/skills/rech-skill-creator/`:

```
rech-skill-creator/
├── .gitignore                      (__pycache__/, *.pyc, .pytest_cache/)
├── SKILL.md
├── contract_template.yaml
├── references/
│   ├── acceptance-cases.md
│   ├── contract-schema.md
│   ├── defect-register.md
│   ├── eval-manifest-format.md
│   ├── gate-semantics.md
│   ├── skills-api-scope.md
│   └── reconstruction-report-v1.md   (este arquivo)
├── scripts/
│   ├── rsc_common.py
│   ├── schema_validator.py
│   ├── package_validate.py
│   ├── skills_api_validate.py
│   ├── snapshot_manager.py
│   ├── eval_isolation_check.py
│   ├── run_executor.py
│   ├── valid_run_gate.py
│   └── package_release_gate.py       (9 scripts — não há aggregation.py
│                                       separado; a lógica de agregação
│                                       vive dentro de valid_run_gate.py e
│                                       package_release_gate.py, já que
│                                       "aggregation" não foi nomeado
│                                       individualmente na lista mínima de
│                                       componentes e um arquivo isolado só
│                                       para isso não agregaria clareza)
└── tests/
    ├── conftest.py
    ├── fixtures/
    │   ├── eval_manifest_valid.yaml
    │   ├── eval_manifest_multiline.yaml
    │   └── minimal_skill_pkg/ (SKILL.md, contract.yaml, references/notes.md, scripts/noop.py)
    └── test_*.py (9 arquivos, 52 casos de teste)
```

**Desvio da lista literal do usuário**: `tests/fixtures/runs/run-1/` e
`run-1-missing-eval/` não existem como diretórios estáticos commitados.
Decisão deliberada: run directories (`result.json`/`run_meta.json`) são
gerados dinamicamente em `tmp_path` por cada teste, via o helper
`run_writer` em `conftest.py` (para testes de gate que precisam de controle
exato sobre outcomes, incluindo forçar `RUN_INVALID`) ou via o `run_executor.py`
real (para o teste end-to-end). Manter fixtures estáticas de `result.json`
exigiria mantê-las manualmente em sincronia com o schema real do
`run_executor.py` — o helper dinâmico elimina esse risco de desatualização
silenciosa, e ainda assim satisfaz "não criar arquivos só para preencher
estrutura."

## B. Architecture reconstructed

Pipeline de 13 estágios implementado exatamente como especificado:
`DISCOVER → CONTRACT → RISK CLASSIFICATION → DRAFT → SCHEMA VALIDATION →
EVAL ISOLATION → SNAPSHOT/HASH DECISION INPUTS → RUN EXECUTION →
VALID_RUN_GATE → AGGREGATION → ARTIFACT_INTEGRITY_GATE →
PACKAGE_RELEASE_GATE → PACKAGE`. Ver `SKILL.md` para o diagrama completo e
`references/gate-semantics.md` para o algoritmo prosa de cada gate.

Divergência deliberada do padrão do ecossistema (5 skills existentes são
100% markdown, zero código): esta é a primeira skill com scripts Python
reais — explicitamente documentado no `SKILL.md`, seção "Divergência
deliberada do padrão do ecossistema", mesmo padrão que `rech-deep-audit` usa
para marcar suas próprias extensões de RAF.

## C. Known-defect coverage

Ver seção "KNOWN DEFECTS" abaixo para a matriz completa.

## D. Contract/schema

`contract_template.yaml` contém as 18 chaves de topo exigidas (`skill_id`
até `metadata`), verificado mecanicamente por
`test_contract_template_matches_required_key_set`. `schema_validator.py`
valida instâncias contra o mesmo conjunto, incluindo `metadata` como
mapeamento (defeito #9) e `severity`/`minimum_evidence_level` restritos à
escala RAF (nunca vocabulário próprio). Detalhe campo a campo em
`references/contract-schema.md`.

## E. Eval isolation

`eval_isolation_check.py` implementado com a família de status
`PASS|PARTIAL|UNVERIFIED` (mais `NOT_APPLICABLE`, reservado para uso
futuro/outros contextos). `--scope` ausente → `UNVERIFIED`; escopo parcial
ou com overlap de recurso compartilhado detectado → `PARTIAL`; nunca `PASS`
sem escopo explícito, completo e sem overlap (defeito #7). Sugestão de
escopo automática (quando ausente) é anexada como diagnóstico, nunca
substitui o valor exigido (`auto/infer = diagnostic only`).

## F. Snapshot/integrity model

`snapshot_manager.py` congela `eval_manifest.yaml` (canonicalizado,
SHA-256) e grava `decision_input_manifest.json` cobrindo 6 categorias
(`ORIGINAL`, `PREVIOUS`, `CANDIDATE`, `EVAL_MANIFEST`, `CONTRACT`, `CONFIG`)
mais `EVAL_DEFINITIONS_FIXTURES`. Diretórios usam hash Merkle-lite (nunca
tarball); YAML/JSON são canonicalizados antes do hash (cosmético não
registra como mudança). `ORIGINAL`/`PREVIOUS` ausentes (skill nova, sem
histórico) são gravados como ausência explícita hasheada
(`{"kind":"none","sha256":null}`), decisão confirmada com o usuário.
`ARTIFACT_INTEGRITY_GATE` recomputa e compara as 6 categorias com o mesmo
laço uniforme (defeito #3) — ver `references/eval-manifest-format.md` e
`references/gate-semantics.md`.

Durante a implementação, os testes do próprio pipeline expuseram que
`CANDIDATE` precisa ser um subdiretório genuinamente isolado
(`workdir/candidate/`), separado de `eval_manifest.yaml`/`contract.yaml`/
`snapshot/`/`runs/` — caso contrário o hash de `CANDIDATE` fica acoplado a
arquivos que já são rastreados separadamente, e `runs/` (criado *depois* do
freeze) invalidaria retroativamente o próprio snapshot que acabou de criar.
Documentado em `tests/conftest.py::pipeline_workdir`.

## G. Run semantics

`run_executor.py` recusa rodar sem manifesto congelado. Cada eval resolve a
`PASS`/`FAIL`/`RUN_INVALID` (timeout, exceção de infra, ou
`execution_mode` não executável neste harness offline). `RUN_INVALID` nunca
conta como PASS nem como FAIL funcional (defeito #4-adjacente, mesmo
princípio). `primary`/`baseline_ref` sempre lidos de campo explícito do
manifesto, nunca por ordem de lista ou diretório.

## H. VALID_RUN_GATE

Algoritmo completo em `references/gate-semantics.md`. Cobre: eval declarado
faltante → FAIL (defeito #2); `RUN_INVALID` como terceiro bucket; runs
válidas insuficientes (`min_valid_runs=1` default, confirmado com o
usuário) → FAIL; **achado adicional durante a implementação, fora da lista
original**: uma run cujo `manifest_sha256` gravado não bate com o snapshot
atualmente congelado (manifesto foi re-congelado desde que a run rodou) é
tratada como estruturalmente incompleta ("stale"), nunca aceita
silenciosamente — corrigido e testado
(`test_stale_manifest_run_is_rejected`), documentado em
`references/defect-register.md` como observação adicional.

## I. ARTIFACT_INTEGRITY_GATE

Cobre as 6 categorias uniformemente, sem caso especial para `CANDIDATE`
(defeito #3) — testado parametricamente, uma mutação por categoria por vez,
confirmando que só a categoria mutada é sinalizada.

## J. PACKAGE_RELEASE_GATE

`RELEASABLE` só com os dois sub-gates em PASS; `BLOCKED` citando qual gate
falhou; `INCONCLUSIVE` se um sub-gate não pôde nem ser calculado. Nome
interno sempre `package_release_gate` — nunca `release_gate` sozinho,
verificado mecanicamente via AST (defeitos #6/#11), não só por convenção.

## K. SKILLS_API validation

`skills_api_validate.py` nunca retorna PASS vazio (defeito #4). 8 checks
offline reais (frontmatter, naming, estrutura, YAML, links internos) +
3 sempre `NOT_APPLICABLE` (`upload_registration`, `live_routing`,
`size_report`). `overall_status()` nunca é `PASS` enquanto houver
`UNVERIFIED` pendente. Escopo completo em `references/skills-api-scope.md`.

## L. Packaging validation

`package_validate.py` cobre presença de `SKILL.md`, parse de frontmatter,
campos obrigatórios, tipos de arquivo permitidos por pasta, ausência de
arquivos ocultos/estranhos, e YAML bem-formado — todo parsing via
`rsc_common.load_yaml()`/`load_yaml_str()` exclusivamente (defeito #10),
provado com fixture de block scalar multiline com linha-isca.

## M. Tests

52 testes, `pytest -v` 100% verde (evidência completa em
`tests/` — comando: `cd .claude/skills/rech-skill-creator && python3 -m
pytest tests/ -v`). Cobre os 12 requisitos mínimos pedidos mais os 10
defeitos numerados mais 1 achado adicional (stale manifest) mais testes de
regressão auxiliares (cosmético-não-flagado, run pós-snapshot não perturba
candidate, etc.).

## N. Routing validation

`references/acceptance-cases.md`: 11 casos, 7 `HARD ACCEPTANCE`. Cobre
triggers positivos, redirecionamento para as 5 skills irmãs (incluindo a
distinção explícita entre `PACKAGE_RELEASE_GATE` e `rech-release-gate`), e
recusa de tocar qualquer skill travada. Não executado automaticamente nesta
rodada (são casos de comportamento de roteamento do próprio Claude, não
scripts) — ver seção Q.

## O. Structural validation

`test_package_validate.py` + `test_skills_api_validate.py` confirmam que a
fixture `minimal_skill_pkg` (usada por toda a suíte) passa em 100% dos
checks estruturais, e que violações deliberadas (arquivo tipo errado,
arquivo oculto estranho, nome de diretório não-kebab-case, `redirect_to`
não resolvido) são cada uma detectada e nomeada corretamente.

## P. Behavioral validation

`test_pipeline_end_to_end.py` roda o pipeline completo (isolation → freeze
→ execução real via subprocess → os dois gates → release gate) contra a
fixture, confirmando `RELEASABLE` no caminho feliz, e `BLOCKED` citando o
gate certo em dois caminhos de falha (mutação pós-snapshot; nenhuma run
executada).

## Q. Remaining limitations

- Nenhum provider de IA real, nenhum backend/proxy, nenhuma exportação além
  do que já existia — fora de escopo desta reconstrução, não pedido.
- `references/acceptance-cases.md` desta skill não tem um harness
  automatizado que realmente invoque um Claude para testar roteamento —
  como as 5 skills irmãs, esses casos são material de revisão humana/futura
  automação via `EVAL_MANIFEST` com `execution_mode: claude_invocation`,
  que `run_executor.py` já classifica honestamente como `RUN_INVALID`
  (não executável neste harness) em vez de fingir.
- `size_report` em `skills_api_validate.py` não tem um limite real
  documentado para pontuar contra — reportado como fato, nunca como
  PASS/FAIL, e sinalizado como tal.
- Não recuperamos os 4 artefatos originais citados no kickoff histórico do
  ecossistema (`SCHEMA_V1.1.json`, `ENGINE_RULES_V1.md`, `PROMPT_WORK.md`,
  `Rech_Passagem_TEMPLATE_CANONICO_v3.1.docx`) — irrelevantes para esta
  reconstrução (são de outro projeto do ecossistema, RechShift), citado
  aqui só para registro de proveniência caso a menção apareça em auditoria
  futura.
- Push feito para `feat/rech-skill-creator-v1` (recriada a partir da main
  atual, com `--force-with-lease`, já que a branch remota tinha histórico
  não-relacionado/obsoleto). **Sem merge** — aguardando autorização
  explícita.

---

## KNOWN DEFECTS — matriz PASS/FAIL

| # | Defeito | Correção | Teste (evidência) | Resultado |
|---|---|---|---|---|
| 1/8 | EVAL_MANIFEST congelado antes de qualquer run | `snapshot_manager.freeze()` + `run_executor.py` recusa sem snapshot | `test_snapshot_manager.py::test_manifest_snapshot_created_before_run_executor_can_run` | **PASS** |
| 2 | VALID_RUN_GATE falha com eval declarado faltante | Checagem estrutural antes de ler outcomes | `test_valid_run_gate.py::test_missing_required_eval_blocks_gate` | **PASS** |
| 3 | ARTIFACT_INTEGRITY_GATE protege todos os inputs | Laço uniforme sobre 6 categorias | `test_artifact_integrity_gate.py::test_integrity_covers_all_named_inputs[*]` (5 casos parametrizados) | **PASS** |
| 4 | SKILLS_API nunca PASS vazio | Checks com evidência; NOT_APPLICABLE explícito | `test_skills_api_validate.py::test_no_bare_pass_without_evidence` | **PASS** |
| 5 | contract_template é o contrato completo | Chaves obrigatórias verificadas mecanicamente | `test_schema_validator.py::test_contract_template_matches_required_key_set` | **PASS** |
| 6/11 | PACKAGE_RELEASE_GATE exige os 2 gates, sem ambiguidade de nome | Composição + checagem AST do identificador | `test_package_release_gate.py::test_blocked_without_valid_run_gate_pass`, `test_blocked_without_artifact_integrity_gate_pass`, `test_no_naming_ambiguity` | **PASS** |
| 7 | EVAL_ISOLATION nunca PASS com scope ausente/insuficiente | Família UNVERIFIED/PARTIAL/PASS | `test_eval_isolation_check.py::test_missing_scope_yields_unverified_not_pass`, `test_insufficient_scope_yields_partial_not_pass` | **PASS** |
| 9 | Schema aceita metadata | Campo obrigatório + validação de tipo | `test_schema_validator.py::test_metadata_field_accepted`, `test_metadata_missing_is_rejected` | **PASS** |
| 10 | package_validate parseia YAML multiline | Parsing exclusivo via PyYAML safe_load | `test_package_validate.py::test_multiline_block_scalar_parsed_correctly` | **PASS** |
| extra | Run contra manifesto obsoleto (stale) não é aceita | Checagem de manifest_sha256 por run | `test_valid_run_gate.py::test_stale_manifest_run_is_rejected` | **PASS** |

**10/10** defeitos numerados cobertos, mais 1 achado adicional corrigido
durante a implementação. `pytest -v` completo: **52 passed, 0 failed**.

---

## VERDICT: LOCKED CANDIDATE

Todos os defeitos conhecidos têm correção com teste passando. O pipeline
completo (`test_pipeline_end_to_end.py`) funciona ponta a ponta nos
caminhos feliz e bloqueado. Nenhum arquivo fora de
`.claude/skills/rech-skill-creator/` foi alterado. A divergência do padrão
do ecossistema (código executável) está explicitamente documentada, não
escondida.

Ressalva não-bloqueante: as regras de roteamento (`acceptance-cases.md`)
não foram exercitadas por um harness automatizado nesta rodada — são
material de revisão humana, como acontece com as 5 skills irmãs.
