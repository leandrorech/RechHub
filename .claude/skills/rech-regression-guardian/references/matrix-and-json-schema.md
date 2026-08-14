# Matriz de regressão — formato completo e schema JSON

## Estrutura do relatório em Markdown

```markdown
# Regression Guardian — <Projeto> — <data>

CANDIDATE: <branch>@<hash> | diff colado | working tree
BASELINE: main@<hash ou tag> | descrito pelo usuário (não verificado via git)
EVALUATION SCOPE: <arquivos/módulos/capabilities cobertos por esta avaliação>
UPSTREAM FIX REPORT: <FIX-ID de rech-fix, se aplicável | nenhum>

## Matriz

| ID | Área | Invariante/Funcionalidade | Baseline | Candidato | Evidência | Nível | Classification | Confidence | Verification |
|---|---|---|---|---|---|---|---|---|---|
| INV-RD-VENT-003 | Ventilação | Não propagar parâmetros após extubação | PASS | FAIL | teste tests/clinicalstate/vent.test.ts + diff L120-134 | 3 (teste automatizado) | REGRESSION | HIGH | COMPLETE |
| CAP-RD-UI-004 | Preview | Preview continua acessível | PASS | PASS | Playwright | 3 | PASS | HIGH | COMPLETE |
| REG-RD-012 | Upload | ≥10 anexos não quebra geração | PASS | PASS | golden case (verificado em tests/golden/) | 2 | PASS | HIGH | COMPLETE |
| CAP-RSH-002 | Reconciliação | Item mantém proveniência tipada | N/A | N/A | golden case: N/A — tests/golden/ não existe neste repo | — | INCONCLUSIVE | LOW | MANUAL_REQUIRED |
| SAFE-RD-002 | Validação | Alerta bloqueante em estado ventilatório conflitante | DEMONSTRATED HISTORICAL BEHAVIOR (nível 6) | ausente | inspeção de código | 6 | REGRESSION | MEDIUM | MANUAL_REQUIRED |

## Mudanças (CHANGE) — não são regressão

### CHANGE-017 — Antitrombóticos removidos da interface
Baseline: presentes | Candidato: ausentes | Diff: SIM
CLASSIFICATION: CHANGE — mudança explicitamente aprovada (motivo: <razão fornecida pelo usuário>)

## Invariantes candidatos descobertos (sugestão, não promovido)

### CANDIDATE — <descrição>
Evidência: <finding/commit/teste>
Confiança: <HIGH/MEDIUM/LOW>

## Regressões conhecidas pré-existentes (KNOWN REGRESSION — não geradas por esta mudança)

(Itens que já eram bug antes do candidato — registrados para não confundir com a mudança atual, e para não serem esquecidos. Não entram no cômputo do veredito global desta avaliação.)

## Veredito global

REGRESSION VERDICT: REGRESSION | INCONCLUSIVE | CHANGE | PASS

<justificativa curta: por que este veredito, seguindo a precedência REGRESSION > INCONCLUSIVE > CHANGE > PASS; contagem de itens por classificação; nota explícita de que esta skill não decide bloqueio de release>
```

## Regras de preenchimento

- Toda linha da matriz precisa citar **evidência concreta** (arquivo de teste, commit, finding RAF, nome do fixture) — nunca deixar a coluna de evidência vaga tipo "parece que sim".
- A coluna "Nível" usa os números 1–7 da `BASELINE EVIDENCE HIERARCHY` (1 = invariante formal, mais confiável; 7 = user recollection, menos confiável). Inferência de código nunca ocupa esta coluna sozinha — se for a única fonte disponível, o item vai para `INCONCLUSIVE`.
- `Classification` só aceita os quatro valores: `REGRESSION`, `CHANGE`, `PASS`, `INCONCLUSIVE`. Não usar `BLOCK`, `PASS COM RESSALVAS` ou `MANUAL REVIEW` como substitutos.
- `Confidence` (`HIGH`/`MEDIUM`/`LOW`) deriva do nível de evidência: nível 1–2 tende a HIGH, nível 3–4 tende a MEDIUM/HIGH conforme o caso, nível 5–7 tende a MEDIUM/LOW, e nível 7 sozinho nunca sustenta HIGH.
- `Verification` (`COMPLETE`/`LIMITED`/`MANUAL_REQUIRED`) descreve o quanto a checagem foi automatizada — independente da classificação. Um item pode ser `PASS` com `MANUAL_REQUIRED` (confirmado por inspeção humana, não por teste).
- Não omitir a seção "Mudanças (CHANGE)" mesmo quando vazia — declare explicitamente "Nenhuma mudança (CHANGE) registrada nesta análise" para deixar claro que a ausência foi verificada, não esquecida.
- Itens `KNOWN REGRESSION` (bugs pré-existentes, não causados por este diff) nunca elevam o veredito global para `REGRESSION` — eles são registrados separadamente, precisamente para não contaminar a avaliação da mudança atual.

## Schema JSON (saída opcional, só quando pedida)

```json
{
  "verdict": "REGRESSION",
  "candidate": "feature/rechdocs-vent-fix@def456",
  "baseline": "main@abc123",
  "evaluation_scope": ["src/clinicalstate/resolveVentilatorio.ts"],
  "upstream_fix_report": "FIX-RD-042",
  "generated_at": "2026-08-10T12:00:00-03:00",
  "checks": [
    {
      "id": "INV-RD-VENT-003",
      "area": "Ventilação",
      "description": "Não propagar parâmetros após extubação",
      "category": "invariant",
      "severity": "critical",
      "baseline_result": "pass",
      "candidate_result": "fail",
      "evidence": "tests/clinicalstate/vent.test.ts; diff L120-134",
      "evidence_level": 3,
      "classification": "regression",
      "confidence": "high",
      "verification": "complete"
    }
  ],
  "changes": [
    {
      "id": "CHANGE-017",
      "description": "Antitrombóticos removidos da interface",
      "baseline": "presentes",
      "candidate": "ausentes",
      "approved_reason": "<razão fornecida pelo usuário>"
    }
  ],
  "candidate_invariants": [
    {
      "description": "resolveVentilatorio() não deve propagar parâmetros após extubação",
      "evidence": ["RAF-017", "commit abc123", "tests/clinicalstate/vent.test.ts"],
      "confidence": "high"
    }
  ],
  "known_pre_existing_regressions": []
}
```

Campos obrigatórios em `checks[]`: `id`, `category` (`invariant`|`capability`|`safeguard`|`known_regression`), `severity` (`critical`|`high`|`medium`|`low`), `baseline_result`, `candidate_result`, `evidence`, `evidence_level` (1–7), `classification` (`regression`|`change`|`pass`|`inconclusive`), `confidence` (`high`|`medium`|`low`), `verification` (`complete`|`limited`|`manual_required`).

O campo `verdict` de topo aceita exatamente os mesmos quatro valores de `classification`, aplicando a precedência `regression > inconclusive > change > pass` sobre o conjunto de `checks[]`.

Este schema existe para permitir integração futura com GitHub Actions, scripts, dashboards, uma futura `rech-release-gate`, ou PR checks — não é necessário gerar sempre, só quando o consumo for por outra ferramenta/máquina.
