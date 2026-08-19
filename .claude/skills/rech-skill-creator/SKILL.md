---
name: rech-skill-creator
description: "Cria e valida pacotes de skill do Claude Code com um pipeline sequencial de contrato, schema, isolamento de evals, snapshot, execução real, integridade e package release gate. Use ao criar uma skill do zero, validar um pacote antes de publicar ou investigar por que uma skill não está sendo escolhida. Exige evidência mecânica para PASS, congela e hasheia os decision inputs antes das runs e reporta UNVERIFIED, NOT_APPLICABLE, PARTIAL, BLOCKED ou INCONCLUSIVE quando a verificação não é possível. Usa somente a taxonomia RAF. Não decide release de produtos RECH, não audita conteúdo clínico, não corrige skills existentes e não altera as cinco skills travadas: rech-deep-audit, rech-fix, rech-regression-guardian, rech-release-gate e rech-repo-context."
---

# RECH Skill Creator

## Missão e fronteiras

A pergunta que esta skill responde:

> *"Este pacote de skill está estrutural e contratualmente pronto para ser
> empacotado, com evidência mecânica e não-simulável de que os gates foram
> satisfeitos — ou não está?"*

Ela não é uma skill de "escrever uma skill melhor" nem de auditoria de
qualidade de conteúdo de outra skill já existente. Ela também não decide se
uma mudança em produto RECH (RechDocs, RechStudy, RechSupps, RechTrauma,
RechShift) pode mergear — essa pergunta é do `rech-release-gate`, um skill
completamente diferente, embora o nome do gate interno desta skill
(`PACKAGE_RELEASE_GATE`) seja deliberadamente parecido. Ver "Relação com as
demais skills" abaixo para a distinção explícita.

## Divergência deliberada do padrão do ecossistema

As 5 skills hoje travadas no RechHub (`rech-deep-audit`, `rech-fix`,
`rech-regression-guardian`, `rech-release-gate`, `rech-repo-context`) são
100% markdown/instruções — nenhuma delas tem código executável. Esta é a
**primeira** skill do ecossistema a embarcar scripts Python reais em
`scripts/`, implementando gates programáticos de verdade.

Isso é intencional, não uma mudança silenciosa de padrão: o motivo de
`rech-skill-creator` existir é impedir exatamente o tipo de validação
"simulada" que uma skill puramente baseada em instruções não consegue
garantir mecanicamente — por exemplo, `SKILLS_API` nunca pode retornar um
`PASS` vazio (defeito conhecido #4). Um LLM seguindo instruções em prosa pode,
sob pressão, "decidir" que um check passou sem executá-lo de fato. Um script
que hasheia, compara e falha de forma determinística não pode.

## Fronteira dura

```
FIRMED:
- Nunca altera nenhum arquivo das 5 skills já travadas.
- Nunca inicia outra skill nova por conta própria.
- Nunca inventa taxonomia de severidade/evidência/status paralela a RAF.
- Nunca emite PASS sem evidência mecânica real — UNVERIFIED / NOT_APPLICABLE
  / PARTIAL / BLOCKED / INCONCLUSIVE são resultados legítimos e frequentes.
- Nunca infere PRIMARY/BASELINE por ordem de lista — sempre por campo
  explícito no manifesto.
- Nunca conta um RUN_INVALID (timeout, exceção de infra) como PASS
  funcional, nem como FAIL funcional — é um terceiro estado.
```

## RAF é obrigatório

Qualquer campo de classificação (`severity`, `evidence_level`) neste pacote
usa exclusivamente a escala RAF definida em
`rech-deep-audit/references/finding-schema-and-raf-mapping.md`:
`BLOCKER|CRITICAL|HIGH|MEDIUM|LOW` para severidade, `E0`-`E5` para força de
evidência. Uma tentativa anterior desta mesma skill propôs uma taxonomia de 7
rótulos própria e foi explicitamente rejeitada por fragmentar a linguagem de
governança do ecossistema — não repetir esse erro.

## Pipeline

```
DISCOVER
  ↓
CONTRACT               (contract_template.yaml → contract.yaml da skill candidata)
  ↓
RISK CLASSIFICATION    (execution_environment, risk_side_effects do contrato)
  ↓
DRAFT
  ↓
SCHEMA VALIDATION       (schema_validator.py)
  ↓
EVAL ISOLATION          (eval_isolation_check.py — pré-check obrigatório;
  ↓                      resultado não-PASS trava o pipeline até override humano explícito)
SNAPSHOT / HASH DECISION INPUTS   (snapshot_manager.py — SHA-256 de
  ↓                                 ORIGINAL/PREVIOUS/CANDIDATE/EVAL_MANIFEST/
  ↓                                 CONTRACT/EVAL_DEFINITIONS_FIXTURES/CONFIG)
RUN EXECUTION           (run_executor.py — harness/wrapper/adapter; só lê o
  ↓                       manifesto CONGELADO, nunca o arquivo de trabalho)
VALID_RUN_GATE          (valid_run_gate.py)
  ↓
AGGREGATION
  ↓
ARTIFACT_INTEGRITY_GATE (artifact_integrity_gate.py)
  ↓
PACKAGE_RELEASE_GATE    (package_release_gate.py — RELEASABLE | BLOCKED | INCONCLUSIVE)
  ↓
PACKAGE
```

## Equações centrais

```
SKILL_SCHEMA ⟂ EXECUTION_ENVIRONMENT
   O schema declarado da skill e o ambiente onde ela de fato roda são
   preocupações independentes — nunca fundidas silenciosamente.

SEVERITY ⟂ GATE
   A severidade de um achado nunca é, por si só, o que decide PASS/FAIL de
   um gate. Cada gate tem sua própria lógica explícita (ver
   references/gate-semantics.md).

AUTO/INFER = DIAGNOSTIC ONLY
   Qualquer sugestão calculada automaticamente (ex.: escopo de isolamento
   sugerido quando --scope foi omitido) é só um diagnóstico anexado ao
   resultado — nunca substitui o valor explícito exigido para PASS.
```

## Input contract

```
RECH SKILL CREATOR INPUT

MODO: DISCOVER | VALIDATE_PACKAGE | RUN_PIPELINE

Para DISCOVER/CONTRACT:
  GOAL: <o que a skill deve fazer>
  TRIGGERS: <quando deve ser invocada>

Para VALIDATE_PACKAGE:
  PACKAGE_DIR: <caminho do pacote de skill a validar>
  SKILLS_ROOT: <opcional — .claude/skills/, para checar redirect_to>

Para RUN_PIPELINE:
  WORKDIR: <diretório com candidate/, eval_manifest.yaml, contract.yaml>
  SCOPE: <obrigatório para EVAL_ISOLATION — lista de eval_id ou arquivo>
  MIN_VALID_RUNS: <opcional, default 1>
```

## Contrato de dados

`contract_template.yaml` é o contrato completo aprovado — ver
`references/contract-schema.md` para o detalhamento campo a campo. Toda
instância `contract.yaml` produzida por esta skill é validada por
`schema_validator.py` contra o mesmo conjunto de chaves obrigatórias.

`eval_manifest.yaml` declara os evals de uma skill candidata — ver
`references/eval-manifest-format.md`. Todo manifesto é **congelado e
hasheado antes de qualquer run** (`snapshot_manager.py`); nenhum estágio
downstream pode ler o arquivo de trabalho ao vivo, só a cópia congelada.

## Os três gates

Ver `references/gate-semantics.md` para o algoritmo completo de cada um.
Resumo:

- **`VALID_RUN_GATE`** — `PASS`/`FAIL` sobre as runs reais em disco contra o
  manifesto congelado. Eval declarado faltando numa run = `FAIL` imediato.
  `RUN_INVALID` nunca conta como `PASS` nem como `FAIL` funcional.
- **`ARTIFACT_INTEGRITY_GATE`** — `PASS`/`FAIL` recomputando o hash de
  **todos** os decision inputs (não só `CANDIDATE`) contra o snapshot
  congelado.
- **`PACKAGE_RELEASE_GATE`** — compõe os dois gates acima em
  `RELEASABLE | BLOCKED | INCONCLUSIVE`. Nome interno sempre literal —
  nunca abreviado para `release_gate` (colidiria conceitualmente com o skill
  irmão `rech-release-gate`, que decide outra coisa).

## SKILLS_API — o que é checável offline

`skills_api_validate.py` nunca retorna `PASS` vazio. Ver
`references/skills-api-scope.md` para a lista completa do que é checável sem
rede (frontmatter, naming, estrutura de arquivos, YAML bem-formado, links
internos) versus o que é sempre `NOT_APPLICABLE` neste sandbox
(`upload_registration`, `live_routing`).

## Relação com as demais skills

- **rech-deep-audit** audita qualidade/segurança de conteúdo clínico ou
  código de um projeto RECH. Esta skill nunca faz isso — ela audita a
  estrutura/contrato de um **pacote de skill**, não o conteúdo clínico de
  nada.
- **rech-fix** corrige um bug já diagnosticado num projeto RECH. Esta skill
  nunca corrige as 5 skills travadas nem qualquer outro código de produto.
- **rech-regression-guardian** compara candidate vs. baseline de uma mudança
  de produto RECH. `ARTIFACT_INTEGRITY_GATE` também compara hashes, mas
  sobre decision inputs de um build de skill, não sobre comportamento
  clínico de um produto.
- **rech-release-gate** decide se uma mudança de **produto RECH** pode
  mergear/lançar. `PACKAGE_RELEASE_GATE` decide se um **pacote de skill**
  está pronto para empacotar. Duas perguntas diferentes; nomes parecidos de
  propósito para deixar claro que são a mesma *forma* de decisão (gate
  binário/composto), aplicada a domínios diferentes — nunca a mesma decisão.
- **rech-repo-context** estabelece o estado atual de um repositório. Esta
  skill não estabelece estado de repositório — ela valida um pacote
  específico.

## Output contract

```
RECH-SKILL-CREATOR RECONSTRUCTION REPORT
  (ou, para uma validação pontual: RECH-SKILL-CREATOR VALIDATION RESULT)

A. Files created
B. Architecture reconstructed
C. Known-defect coverage
D. Contract/schema
E. Eval isolation
F. Snapshot/integrity model
G. Run semantics
H. VALID_RUN_GATE
I. ARTIFACT_INTEGRITY_GATE
J. PACKAGE_RELEASE_GATE
K. SKILLS_API validation
L. Packaging validation
M. Tests
N. Routing validation
O. Structural validation
P. Behavioral validation
Q. Remaining limitations

KNOWN DEFECTS: <matriz PASS/FAIL, um teste real citado por linha>

VERDICT: LOCKED CANDIDATE | NEEDS REVISION
```

## Safeguards (um por defeito conhecido, ver references/defect-register.md)

1. Nenhum run executa contra um manifesto não congelado — `run_executor.py`
   recusa (`RuntimeError`) se `snapshot/eval_manifest.canonical.yaml` não
   existir.
2. Eval declarado ausente numa run bloqueia `VALID_RUN_GATE` antes mesmo de
   ler outcomes.
3. `ARTIFACT_INTEGRITY_GATE` roda o mesmo laço de recomputar-e-comparar sobre
   as 6 categorias de decision input, sem nenhum caso especial para
   `CANDIDATE`.
4. `SKILLS_API` nunca retorna PASS vazio — cada check tem evidência; checks
   fora de escopo offline são `NOT_APPLICABLE` explícito.
5. `contract_template.yaml` contém todas as chaves obrigatórias — checado
   mecanicamente por `test_contract_template_matches_required_key_set`.
6. `PACKAGE_RELEASE_GATE` exige os dois sub-gates em `PASS`; o identificador
   `release_gate` nunca aparece sozinho no módulo (checado via AST).
7. `EVAL_ISOLATION` nunca dá `PASS` com `--scope` ausente ou insuficiente.
9. Schema aceita e valida `metadata` como mapeamento.
10. Todo parsing de YAML passa por `rsc_common.load_yaml()` — nenhum
    scanner de linha próprio em nenhum lugar do pacote.

## Referências

- `references/acceptance-cases.md` — casos de trigger/near-miss desta
  própria skill, incluindo os `HARD ACCEPTANCE`.
- `references/contract-schema.md` — detalhamento campo a campo de
  `contract_template.yaml`.
- `references/eval-manifest-format.md` — formato do `EVAL_MANIFEST` e
  semântica de congelamento.
- `references/gate-semantics.md` — algoritmo prosa completo dos três gates.
- `references/skills-api-scope.md` — o que `skills_api_validate.py` checa
  offline versus o que reporta `NOT_APPLICABLE`.
- `references/defect-register.md` — os 10 defeitos conhecidos, cada um com
  correção e teste que prova a correção.
- `references/reconstruction-report-v1.md` — o relatório final desta
  reconstrução (seções A-Q, matriz de defeitos, veredito).
