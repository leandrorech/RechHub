# Output contract — RECH GITHUB SCOUT REPORT

```
RECH GITHUB SCOUT REPORT

PROBLEM / CAPABILITY:
TARGET RECH PROJECT:
REPO CONTEXT STATUS:        REQUIRED | RECOMMENDED | NOT NEEDED | OBTAINED

SEARCH SCOPE:

CONSTRAINTS
HARD:
PREFERRED:
CURRENT:
UNKNOWN:

SEARCH STRATEGY:
SOURCES:

CANDIDATES DISCOVERED:
<lista, um CANDIDATE MODEL por item — ver references/candidate-evaluation.md>

ELIMINATED:
<candidato + HARD constraint(s) que causaram a eliminação>

SHORTLIST:
<subconjunto aprofundado>

COMPARISON:
<comparação dos finalistas pelas dimensões do FIT MODEL aplicáveis>

DECISION:
ADOPT | ADAPT | BUILD | INCONCLUSIVE

DECISION RATIONALE:

MISSING / CONFLICTING EVIDENCE:

LIMITATIONS:

RECOMMENDED NEXT STEP:
```

## Regras de preenchimento

- `SEARCH SCOPE`, `SEARCH STRATEGY`, `SOURCES` e `LIMITATIONS` são sempre
  preenchidos, mesmo quando o veredito é `BUILD` — nunca omitidos por
  parecerem "óbvios" quando a decisão é não adotar nada.
- `DECISION` nunca é acompanhada de um score numérico agregado (ver
  `SKILL.md` § "Overengineering guard").
- Quando `DECISION: BUILD`, a frase de "Search completeness" do `SKILL.md`
  é usada literalmente em algum ponto do `DECISION RATIONALE` ou
  `LIMITATIONS` — nunca "não existe solução".
- `RECOMMENDED NEXT STEP` segue a semântica de `HANDOFF` do `SKILL.md`:
  - `ADOPT` → validação isolada / planejamento de integração
  - `ADAPT` → `ADAPTATION GAP` (o que precisa mudar)
  - `BUILD` → `BUILD JUSTIFICATION` (candidatos avaliados e por que foram
    rejeitados)
  - `INCONCLUSIVE` → `MISSING EVIDENCE` + `NEXT VERIFICATION STEP`
