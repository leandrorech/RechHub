# Acceptance cases — rech-regression-guardian

Estes 8 casos não são exemplos narrativos — são acceptance criteria verificáveis. Os casos **1, 2, 4, 6 e 8** são **HARD ACCEPTANCE**: falhar em qualquer um deles resulta em `SKILL ACCEPTANCE: FAIL`, independente do desempenho nos outros. Eles testam os erros conceituais mais perigosos: perder regressão real; chamar mudança aprovada de regressão; inventar certeza com baseline conflitante; transformar lembrança em evidência forte; confiar cegamente no sucesso da `rech-fix`.

---

## Caso 1 — REAL REGRESSION (HARD ACCEPTANCE)

Invariante formal (`RECH_INVARIANTS.md`) + baseline confirmado + candidato demonstram quebra do comportamento protegido.

**Esperado:**
```
CLASSIFICATION: REGRESSION
CONFIDENCE: HIGH
```

**FAIL CRÍTICO:** classificar como `PASS`, `CHANGE` ou `INCONCLUSIVE` quando a evidência de nível 1 (invariante formal) demonstra claramente a quebra.

---

## Caso 2 — APPROVED INTENTIONAL CHANGE (HARD ACCEPTANCE)

Um comportamento previamente protegido (invariante, capability ou teste) mudou, mas existe autorização explícita e documentada para a mudança.

**Esperado:**
```
CLASSIFICATION: CHANGE
```

Nunca `PASS` (perderia o registro de que algo mudou) e nunca `REGRESSION` (ignoraria a aprovação explícita).

**FAIL CRÍTICO:** classificar como `REGRESSION` apesar da aprovação explícita, ou classificar como `PASS` silenciando a mudança sem registro.

---

## Caso 3 — NO REGRESSION

Diff concreto avaliado; o comportamento protegido pelo escopo da avaliação foi preservado integralmente.

**Esperado:**
```
CLASSIFICATION: PASS
```

---

## Caso 4 — CONFLICTING BASELINE EVIDENCE (HARD ACCEPTANCE)

Teste automatizado, documentação e histórico Git entram em conflito entre si sobre qual é o comportamento esperado, sem nenhuma fonte de maior autoridade (invariante formal, golden case) disponível para resolver o conflito.

**Esperado:**
```
CLASSIFICATION: INCONCLUSIVE
```

**Princípio:** a skill não escolhe arbitrariamente qual fonte conflitante "parece mais confiável" — documenta o conflito e retorna `INCONCLUSIVE`.

**FAIL CRÍTICO:** inventar certeza escolhendo uma das fontes conflitantes sem justificativa hierárquica válida (ex.: preferir a documentação só porque é mais recente, sem verificar se ela é de fato autoritativa).

---

## Caso 5 — STALE TEST

Um teste automatizado antigo (nível 3 da hierarquia) exige o comportamento A. Um requisito posterior, explicitamente aprovado (nível 4, ou nível 1 se formalizado como invariante depois), estabelece o comportamento B. O candidato implementa B, e por isso o teste antigo falha.

**Esperado:**
- **não** classificar automaticamente como `REGRESSION` só porque o teste falhou;
- classificar como `CHANGE`;
- sinalizar explicitamente que o teste está desatualizado (stale) e precisa ser atualizado para refletir o requisito aprovado.

```
CLASSIFICATION: CHANGE
STALE TEST DETECTED: <nome do teste> — reflete requisito anterior a <requisito aprovado posterior>, precisa ser atualizado
```

**Princípio:** a hierarquia expressa força evidencial padrão, não uma licença para ignorar aprovação mais recente. Ver "A hierarquia não é absoluta no tempo" em SKILL.md.

**FAIL:** classificar como `REGRESSION` apenas porque o teste (nível 3) falhou, ignorando o requisito aprovado posterior (nível 4 ou superior).

---

## Caso 6 — USER RECOLLECTION ONLY (HARD ACCEPTANCE)

A única evidência disponível de que um comportamento existia é o Leandro relatando "antes funcionava assim" — sem teste, sem golden case, sem documentação, sem demonstração histórica reproduzível.

**Esperado:**
```
CLASSIFICATION: INCONCLUSIVE
CONFIDENCE: LOW
```

Nunca `REGRESSION` de forma assertiva — user recollection sozinha (nível 7) é a evidência mais fraca da hierarquia e nunca sustenta um veredito confiante de que algo quebrou.

**FAIL CRÍTICO:** declarar `REGRESSION` com `CONFIDENCE: HIGH` ou `MEDIUM` baseado unicamente em relato do usuário, sem qualquer evidência verificável por trás.

---

## Caso 7 — UNRELATED DIFF

A mudança concreta avaliada não toca nenhuma capability ou invariante dentro do escopo de avaliação definido.

**Esperado:**
```
CLASSIFICATION: PASS
```
dentro do escopo avaliado — sem expandir a análise para verificar todo o resto do sistema, o que transformaria esta skill em uma auditoria geral (papel de `rech-deep-audit`, não desta skill).

**FAIL:** tentar avaliar aspectos do sistema fora do `EVALUATION SCOPE` declarado, ou recusar-se a dar um veredito por "o diff não toca em nada relevante" — ausência de impacto dentro do escopo é `PASS`, não uma não-resposta.

---

## Caso 8 — FIX LOCAL PASS, BROADER REGRESSION (HARD ACCEPTANCE)

`rech-fix` reportou `STATUS: FIXED` — o problema aprovado foi corrigido, o teste targeted passou, e o `INVARIANT COMPLIANCE CHECK` da `rech-fix` (que cobre apenas o invariante vinculado àquele fix específico) não apontou violação. Mas o mesmo diff, ao ser avaliado nesta skill contra a superfície mais ampla do change-set, quebra um **segundo** invariante ou capability que não estava no escopo do fix original.

**Esperado:**
```
CLASSIFICATION: REGRESSION
```
para o item afetado (o segundo invariante/capability), apesar do relatório da `rech-fix` indicar sucesso.

**Princípio:** `RECH-FIX PASS/FIXED ≠ PROOF OF NO REGRESSION`. O relatório da `rech-fix` é evidência upstream (pode até virar uma linha de alta confiança na matriz para o item que ela de fato cobriu), nunca autoridade final sobre o restante do diff.

**FAIL CRÍTICO:** aceitar `STATUS: FIXED` da `rech-fix` como suficiente para não avaliar o restante da superfície do diff, ou classificar o segundo invariante quebrado como `PASS`/`CHANGE` só porque o `UPSTREAM FIX REPORT` reportou sucesso.

---

## Resultado agregado esperado

```
SKILL ACCEPTANCE: PASS   — se casos 1, 2, 3, 4, 5, 6, 7 e 8 passarem todos
SKILL ACCEPTANCE: FAIL   — se qualquer um dos casos 1, 2, 4, 6 ou 8 falhar,
                            independente do resultado dos demais
```
