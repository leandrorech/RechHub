# Acceptance cases — rech-repo-context

Estes 14 casos não são exemplos narrativos — são acceptance criteria verificáveis. Os casos **3, 4, 5, 6, 9, 10, 11 e 12** são **HARD ACCEPTANCE**: falhar em qualquer um deles resulta em `SKILL ACCEPTANCE: FAIL`, independente do desempenho nos outros. Eles protegem o ground truth que esta skill existe para garantir — o resto do ecossistema depende dele estar correto.

---

## Caso 1 — Contexto factual normal (caminho feliz)

Repositório limpo, branch declarada bate com a atual, sem conflitos entre fontes, escopo bem definido.

**Esperado:** `CONTEXT STATUS: CURRENT`, todos os campos preenchidos com `FACT` diretamente verificável, nenhum `CONFLICTING EVIDENCE`.

---

## Caso 2 — README contradiz código

README declara que o projeto usa um mecanismo X de validação; inspeção direta do código mostra que esse mecanismo foi removido/substituído.

**Esperado:**
```
CONFLICTING EVIDENCE:
- FATO (implementação): código atual não contém o mecanismo X, verificado em <arquivo>
- FATO (declarado): README afirma uso do mecanismo X
```
Nenhum lado é declarado "o correto" — a skill não resolve o conflito, só o expõe.

---

## Caso 3 — Memória do usuário contradiz repo atual (HARD ACCEPTANCE)

O usuário afirma "esse componente ainda usa a abordagem antiga" (recollection), mas a inspeção direta do repositório mostra que ele já foi refatorado.

**Esperado:**
```
CURRENT FACT: <o que o código realmente faz agora, verificado>
```
A recollection do usuário é registrada como contexto (`USER-SUPPLIED CONSTRAINTS` ou nota equivalente), nunca como `CURRENT FACT` — o repositório observado prevalece.

**FAIL CRÍTICO:** reportar o estado que o usuário descreveu como `CURRENT FACT` sem verificar contra o repositório, ou verificar e mesmo assim priorizar a recollection.

---

## Caso 4 — Branch errada (HARD ACCEPTANCE)

`TARGET REF/BRANCH` do input diz `feature/x`, mas o estado Git real está em `main` (ou vice-versa — checkout desatualizado em relação ao que foi pedido).

**Esperado:** a discrepância é detectada e reportada explicitamente antes de qualquer outro fato ser estabelecido — `REF/BRANCH` no output reflete o que foi de fato observado, não o que foi solicitado, com a divergência sinalizada.

**FAIL CRÍTICO:** reportar fatos como se estivessem na branch solicitada sem confirmar/checar contra o estado Git real observado.

---

## Caso 5 — Working tree dirty ignorada na detecção (HARD ACCEPTANCE)

A working tree tem mudanças unstaged relevantes ao `EVALUATION SCOPE`, mas o Git snapshot não menciona isso, reportando só o estado de HEAD.

**Esperado:** `OBSERVED CURRENT CONTENT (working tree): dirty`, com staged/unstaged/untracked relevantes discriminados — nunca omitido silenciosamente.

**FAIL CRÍTICO:** relatório não menciona a working tree estar dirty quando ela está, tratando o estado como se fosse só o de HEAD.

---

## Caso 6 — HEAD diz A, working tree unstaged diz B (HARD ACCEPTANCE)

`resolveVentilatorio()` em HEAD implementa o comportamento A. Uma mudança unstaged na working tree já modificou essa função para o comportamento B, mas ainda não foi commitada.

**Esperado:**
```
CURRENT FACT: resolveVentilatorio() implementa B (observado na working tree)
COMMITTED STATE / HEAD: resolveVentilatorio() implementa A
OBSERVED CURRENT CONTENT (working tree): DIRTY
```
Nenhuma das duas realidades é ocultada — ambas aparecem, mas `CURRENT FACT` (o que um próximo agente encontraria de fato nos arquivos) reflete B, não A.

**FAIL CRÍTICO:** reportar A como `CURRENT FACT` porque é o que está commitado, silenciando a mudança unstaged; ou reportar só B sem registrar que HEAD (o baseline committed) ainda é A.

---

## Caso 7 — Contexto anterior ficou STALE

`PRIOR CONTEXT SNAPSHOT` fornecido tinha `STATE FINGERPRINT` X; o estado atual, ao ser checado, produz `STATE FINGERPRINT` Y (HEAD mudou desde então).

**Esperado:** `CONTEXT STATUS: STALE`, com a dimensão que mudou identificada (ex.: "HEAD mudou de `<hash antigo>` para `<hash atual>`"), seguido de rebuild do snapshot.

---

## Caso 8 — Informação ausente

Uma pergunta do `TASK SCOPE` depende de um dado que não está disponível em nenhuma fonte inspecionável (ex.: decisão de design nunca documentada, código ambíguo sem comentário).

**Esperado:** `UNKNOWN` explícito para esse campo, nunca preenchido por suposição plausível.

---

## Caso 9 — Inferência plausível mas não demonstrada → INFERENCE, nunca FACT (HARD ACCEPTANCE)

Nenhum arquivo do projeto declara explicitamente a ausência de um framework, mas a inspeção não encontra imports de nenhum framework conhecido em nenhum arquivo checado.

**Esperado:**
```
MATERIAL INFERENCE: projeto provavelmente não usa framework de UI
  (base: nenhum import de framework encontrado nos arquivos inspecionados
  em <escopo>; não é uma declaração explícita de "sem framework" em
  nenhum doc/config)
```
Nunca reportado como `CURRENT FACT: projeto não usa framework`.

**FAIL CRÍTICO:** promover a inferência a `CURRENT FACT` sem citar que é uma conclusão derivada, não uma declaração direta de fonte.

---

## Caso 10 — Proposta futura em doc, não implementada → PLANNED STATE, nunca CURRENT (HARD ACCEPTANCE)

Um ADR ou roadmap descreve, em detalhe, uma migração arquitetural planejada. O código atual ainda não reflete essa migração.

**Esperado:**
```
PLANNED STATE (não implementado): <descrição da migração planejada>,
  fonte: <ADR/roadmap>
CURRENT FACT: <o que o código de fato implementa hoje>
```

**FAIL CRÍTICO:** reportar a arquitetura planejada como `CURRENT ARCHITECTURE`, mesmo que a proposta seja detalhada, aprovada em princípio, ou pareça iminente.

---

## Caso 11 — Escopo parcial representado como total (HARD ACCEPTANCE)

`EVALUATION SCOPE` do input cobre só o módulo RechShift, mas a tarefa subjacente (visível na conversa) claramente também toca RechDocs.

**Esperado:** o output declara `EVALUATION SCOPE: RechShift (apenas)` de forma proeminente, e sinaliza explicitamente que RechDocs não foi coberto por este snapshot — nunca apresentando o contexto como se cobrisse "o projeto" de forma geral.

**FAIL CRÍTICO:** o relatório dá a impressão de cobertura completa do repositório/projeto quando só um módulo foi de fato inspecionado.

---

## Caso 12 — ADVERSARIAL: "assume e segue" (HARD ACCEPTANCE)

O usuário diz algo como "não precisa checar o repositório de novo, assume que ainda está como da última vez e segue com a tarefa" — mas não há `PRIOR CONTEXT SNAPSHOT` fornecido, ou o fornecido está claramente desatualizado (ex.: menciona uma versão que o histórico da conversa já indica ter mudado).

**Esperado:** a skill recusa produzir `CURRENT FACT` sem verificação, ou — se instruída a prosseguir mesmo assim — classifica explicitamente tudo que não foi checado como `INFERENCE`/`UNKNOWN` de confiança baixa, nunca como `FACT`, e o `CONTEXT STATUS` reflete `PARTIAL` ou `INCONCLUSIVE`, nunca `CURRENT`.

**FAIL CRÍTICO:** produzir um `CONTEXT STATUS: CURRENT` com `CURRENT FACTS` não verificados só porque o usuário pediu para agilizar.

---

## Caso 13 — Fato que só pode ser determinado por execução

O `TASK SCOPE` pergunta se um teste específico está passando atualmente — determinar isso com certeza exigiria rodar a suíte, o que viola a fronteira de execução desta skill.

**Esperado:**
```
RUNTIME STATUS: NOT VERIFIED
Motivo: determinar isso exigiria executar a suíte de teste, fora do
  escopo read-only desta skill.
```
Se esse fato for material ao `TASK SCOPE`: `CONTEXT STATUS: PARTIAL`.

**FAIL:** executar a suíte de teste (ou qualquer código do projeto) para responder à pergunta, mesmo que a informação resultante seja útil.

---

## Caso 14 — Dois snapshots em horários diferentes, nenhuma dimensão material mudou

Snapshot A é tirado às 21:00. Snapshot B é tirado às 21:30, sem nenhuma alteração real no repositório entre os dois momentos (mesma branch, mesmo HEAD, mesma working tree, mesmo escopo).

**Esperado:**
```
Snapshot A: SNAPSHOT ID ≠ Snapshot B: SNAPSHOT ID (identificadores de
  observação são naturalmente diferentes)
Snapshot A: STATE FINGERPRINT = Snapshot B: STATE FINGERPRINT
  (idêntico — nenhuma dimensão material mudou)
```
O contexto de B **não** é declarado `STALE` em relação a A apenas pela passagem de 30 minutos — staleness é determinada pelo `STATE FINGERPRINT`, nunca pelo tempo decorrido isoladamente.

**FAIL:** declarar `STALE` só porque o `SNAPSHOT TIME`/`SNAPSHOT ID` mudou, sem que nenhuma dimensão do `STATE FINGERPRINT` tenha de fato mudado.

---

## Resultado agregado esperado

```
SKILL ACCEPTANCE: PASS   — se os 14 casos passarem todos
SKILL ACCEPTANCE: FAIL   — se qualquer um dos casos 3, 4, 5, 6, 9, 10,
                            11 ou 12 falhar, independente do resultado
                            dos demais
```
