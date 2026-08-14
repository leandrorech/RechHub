# Template consolidado — RECH RELEASE GATE RESULT

```markdown
# Release Gate — <Projeto> — <data>

DECISION UNIT: CHANGESET | RELEASE
CHANGESET / CHANGESETS: <referência(s) concreta(s)>

## Evidência de entrada

TEST RESULTS: <presente/ausente, resumo>
REGRESSION-GUARDIAN RESULT: <verdict consumido: REGRESSION | CHANGE | PASS | INCONCLUSIVE>
FIX REPORT: <STATUS consumido: FIXED | PARTIALLY_FIXED | BLOCKED | INCONCLUSIVE | ausente>
KNOWN INVARIANTS: ...
APPROVED BEHAVIOR CHANGES: ...
UNRESOLVED ISSUES (herdado): ...
MANUAL VERIFICATION: ...

EVIDENCE COMPLETENESS:
- TEST RESULTS: COMPLETE | PARTIAL | MISSING
- REGRESSION-GUARDIAN RESULT: COMPLETE | PARTIAL | MISSING
- (demais campos conforme aplicável)

## Classificação de achados

HARD BLOCKERS:
1. <achado> — <regra do Passo 2 que se aplica>

WARNINGS:
1. ...

NON-BLOCKING FOLLOW-UPS:
1. <achado> — <ação recomendada, não bloqueante>

INFORMATIONAL FINDINGS:
1. ...

(declarar explicitamente "nenhum" em qualquer categoria vazia, nunca omitir a seção)

## Verificação manual (se aplicável)

Item: ...
Método permitido/adequado: SIM/NÃO
Procedimento reproduzível: SIM/NÃO
Resultado esperado documentado: ...
Resultado observado documentado: ...
Evidência/artefato registrado: SIM/NÃO
→ SATISFAZ o verification contract: SIM/NÃO

## Agregação (se DECISION UNIT: RELEASE)

| Changeset | Veredito próprio |
|---|---|
| A | READY |
| B | READY |
| C | BLOCKED |

Regra aplicada: se algum = BLOCKED → RELEASE BLOCKED; senão se algum
= INCONCLUSIVE → RELEASE INCONCLUSIVE; senão se algum sem avaliação →
RELEASE BLOCKED; senão → RELEASE READY.

## Veredito

VERDICT: READY | BLOCKED | INCONCLUSIVE

JUSTIFICATION: ...

WHAT PASSED: ...
WHAT FAILED: ...
WHAT REMAINS UNRESOLVED: ...

AUTHORIZED TO ADVANCE: <declaração precisa do que está autorizado>
```

## Regras de preenchimento

- `VERDICT` só aceita os três valores. Nunca usar `READY_WITH_CONDITIONS`, `PASS COM RESSALVAS`, `BLOCK` (sem sujeito) ou qualquer híbrido.
- Toda seção de classificação (HARD BLOCKERS / WARNINGS / NON-BLOCKING FOLLOW-UPS / INFORMATIONAL FINDINGS) aparece sempre, mesmo vazia — declarar "nenhum" explicitamente em vez de omitir a seção.
- `AUTHORIZED TO ADVANCE` precisa ser preciso sobre o que exatamente está sendo autorizado — nunca generalizar "release autorizado" quando o `DECISION UNIT` avaliado foi um `CHANGESET` isolado.
- Se `MANUAL VERIFICATION` foi usada para satisfazer algum item, a subseção "Verificação manual" é obrigatória, mesmo que o resto do relatório seja curto — a rastreabilidade do porquê aquela evidência foi aceita precisa sobreviver no registro.
