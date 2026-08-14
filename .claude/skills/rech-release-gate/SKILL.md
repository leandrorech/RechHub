---
name: rech-release-gate
description: "Decide se uma mudança já avaliada por rech-fix e rech-regression-guardian está pronta para avançar para merge ou release — não corrige código, não reavalia causa raiz, não reclassifica regressão. Produz veredito READY, BLOCKED ou INCONCLUSIVE sobre um DECISION UNIT (CHANGESET ou RELEASE), com hard blockers fixos (regressão não resolvida, teste obrigatório falho, evidência obrigatória ausente, invariante violado, INCONCLUSIVE upstream em item relevante) separados de warnings e non-blocking follow-ups. Use quando o usuário perguntar 'posso mergear isso?', 'está pronto pra release?', 'dá o gate final', antes de tag de release, ou depois que rech-regression-guardian produzir veredito com intenção real de avançar. Diferente de rech-fix (corrigiu certo?) e rech-regression-guardian (quebrou algo?): esta pergunta apenas se pode avançar. Nunca converte BLOCKED em READY por pressão de prazo, e nunca trata ausência de evidência obrigatória como sinal de segurança."
---

# RECH Release Gate

## A pergunta que esta skill responde

Três perguntas distintas cobrem o ciclo de vida de uma mudança no ecossistema RECH:

- **rech-fix** pergunta: *"O problema aprovado foi corrigido corretamente?"* (LOCAL CORRECTNESS CHECK)
- **rech-regression-guardian** pergunta: *"Essa mudança quebrou algo previamente estabelecido?"* (CHANGE-SURFACE REGRESSION CHECK)
- **rech-release-gate** pergunta: *"Com base na evidência disponível, esta mudança está suficientemente validada para avançar para merge/release?"*

Esta skill não produz evidência técnica primária nem reexecuta a auditoria — ela consome a evidência upstream (relatórios de `rech-fix` e `rech-regression-guardian`, resultados de teste, verificação manual documentada) e produz apenas o **decision record** do gate: um artefato novo e auditável, mas que nunca reabre ou reavalia diretamente o comportamento do sistema. Se esta skill começar a reinspecionar código ou reinterpretar testes por conta própria, ela deixou de ser um gate e virou uma auditoria paralela — isso é o principal risco de sobreposição a evitar.

Ela **não corrige código**, **não altera teste/requisito/asserção/golden case para obter aprovação**, e **não reinterpreta uma `REGRESSION` como aceitável só porque a mudança é conveniente ou urgente**.

## Passo 0 — Decision unit e input

Toda execução avalia exatamente uma unidade de decisão:

```
DECISION UNIT: CHANGESET | RELEASE
```

**CHANGESET** — um PR, branch, commit, diff ou patch específico. O gate responde só sobre aquilo.

**RELEASE** — o input precisa enumerar explicitamente todos os changesets constituintes:

```
RELEASE:
  changesets:
    - A
    - B
    - C
```

O veredito de um `RELEASE` é agregado a partir do veredito de cada changeset constituinte — nunca inferido por amostragem ou por "os principais já passaram". Ver Passo 5.

```
RELEASE GATE INPUT

DECISION UNIT: <CHANGESET | RELEASE, com changesets enumerados se RELEASE>

CHANGESET / CHANGESETS: <referência(s) concreta(s)>
TEST RESULTS: <obrigatório>
REGRESSION-GUARDIAN RESULT: <obrigatório>
FIX REPORT: <opcional — só se a mudança passou por rech-fix>
KNOWN INVARIANTS: <fornecidos ou descobertos>
APPROVED BEHAVIOR CHANGES: <opcional>
UNRESOLVED ISSUES: <opcional — herdado de FIX REPORT ou REGRESSION-GUARDIAN RESULT>
MANUAL VERIFICATION: <opcional — evidência de verificação manual documentada>
```

`TEST RESULTS` e `REGRESSION-GUARDIAN RESULT` são os únicos campos tratados como evidência obrigatória por padrão para qualquer changeset que toque `INVARIANT` ou `CAPABILITY` conhecidos. Os demais são opcionais e enriquecem a decisão quando disponíveis.

## Passo 1 — Modelo de veredito

```
VERDICT: READY | BLOCKED | INCONCLUSIVE
```

Três estados, não quatro — não existe categoria híbrida como "aprovado com condições". A distinção entre os três é semântica, não de severidade:

- **READY** — zero hard blockers, e nenhuma incerteza que impeça a decisão (`gating uncertainty`). Pode haver `WARNINGS` e `NON-BLOCKING FOLLOW-UPS` — eles não impedem `READY`.
- **BLOCKED** — pelo menos um requisito conhecido do gate não foi satisfeito. O gate sabe exatamente por que não pode autorizar o avanço.
- **INCONCLUSIVE** — o gate não consegue estabelecer a decisão por conflito, ambiguidade de evidência, ou ambiguidade sobre o próprio escopo da decisão. Reservado para um problema epistemológico real — não é sinônimo de "algo está faltando" (isso é `BLOCKED`, ver Passo 2).

A regra que separa `BLOCKED` de `INCONCLUSIVE` é a mais importante desta skill:

```
BLOCKED
= sei que um requisito de release não foi satisfeito.

INCONCLUSIVE
= não consigo determinar se os requisitos foram satisfeitos —
  há evidência, mas ela é conflitante, ambígua, ou o próprio
  escopo da decisão não pode ser estabelecido com confiança.
```

Ausência de uma checagem obrigatória (ex.: `REGRESSION-GUARDIAN RESULT` nunca rodou) é uma **falha de readiness conhecida**, não uma incerteza epistemológica — isso é `BLOCKED`, nunca `INCONCLUSIVE`. `INCONCLUSIVE` fica reservado para casos como: dois relatórios upstream se contradizem diretamente sobre o mesmo item sem forma de resolver qual é autoritativo, ou não é possível determinar com confiança se um item incerto está dentro ou fora do escopo desta decisão.

## Passo 2 — Classificação de achados

Todo achado relevante à decisão é classificado em uma destas quatro categorias, nunca misturadas:

```
HARD BLOCKER        — precisa ser satisfeito antes de avançar
WARNING              — visível, não bloqueia, sem ação exigida
NON-BLOCKING FOLLOW-UP — ação legítima, mas pode acontecer depois do avanço
INFORMATIONAL FINDING  — contexto, sem implicação de ação
```

A classificação acontece **antes** do veredito ser computado, usando as regras fixas abaixo — nunca ao contrário. Não existe discricionariedade para reclassificar um hard blocker como warning ou follow-up para chegar a um veredito mais favorável; em caso de ambiguidade sobre qual categoria um achado pertence, o default é a categoria mais restritiva (`HARD BLOCKER`), nunca a mais permissiva.

### Hard blockers (força `BLOCKED`, sem exceção)

- qualquer `REGRESSION` não resolvida do `regression-guardian`, **independente de severidade**;
- teste obrigatório falhando;
- invariante violado e não resolvido;
- `SCOPE EXPANSION DETECTED` (de `rech-fix`) sem aprovação registrada;
- `INCONCLUSIVE` do `regression-guardian` em qualquer item dentro do `DECISION SCOPE` — não rebaixado por severidade (ver Passo 3);
- evidência obrigatória ausente (`TEST RESULTS` ou `REGRESSION-GUARDIAN RESULT` faltando para changeset que toca `INVARIANT`/`CAPABILITY` conhecidos);
- verificação manual que não satisfaz o verification contract aplicável (ver Passo 4), incluindo verificação vaga ("conferi e está ok") e omissão de automação esperada pelo projeto para aquele invariante.

### Warnings (visível, sem ação exigida)

- `KNOWN REGRESSION` pré-existente, não relacionada a este changeset;
- item `CAPABILITY` com confiança MEDIUM, sem indício de quebra, fora do caminho crítico.

### Non-blocking follow-ups (ação legítima pós-avanço)

- `CANDIDATE INVARIANT` detectado — não é blocker por si só, salvo se outra regra formal exigir sua resolução antes do avanço;
- atualização de documentação para um `CHANGE` de severidade não-crítica (ver regra de default abaixo).

### Informational findings

- `ADJACENT FINDINGS` (de `rech-fix`);
- escopo do que foi avaliado, para contexto.

### Regra de default para documentação de `CHANGE`

Quando um item `CHANGE` do `regression-guardian` ainda não teve seu invariante/spec correspondente atualizado em `RECH_INVARIANTS.md`/`RECH_STATUS.md`, a classificação padrão depende da severidade do item:

- `CHANGE` em item de severidade CRITICAL → `HARD BLOCKER` (a atualização da documentação é parte de tornar o novo comportamento um contrato aplicável; sem ela, a próxima auditoria trataria o novo comportamento como regressão de novo);
- `CHANGE` em item de severidade abaixo de CRITICAL → `NON-BLOCKING FOLLOW-UP` (`FOLLOW_UP: atualizar RECH_INVARIANTS.md/RECH_STATUS.md para refletir <mudança>`).

## Passo 3 — Relação com `rech-regression-guardian`

- **REGRESSION** → hard blocker sempre, a menos que já tenha sido formalmente reclassificada para `CHANGE` pelo próprio guardian (com aprovação humana já registrada no relatório dele). O gate nunca faz essa reclassificação — só verifica se ela já ocorreu de forma legítima.
- **CHANGE** → não vira `READY` automaticamente. Aplica a regra de default do Passo 2 (documentação pendente vira hard blocker ou follow-up conforme severidade).
- **PASS** → necessário, mas não prova segurança absoluta. O gate confere se o `EVALUATION SCOPE` do guardian de fato cobriu o changeset avaliado — `PASS` fora do escopo relevante não sustenta nada sobre o que ficou de fora.
- **INCONCLUSIVE** → hard blocker sempre que o item estiver dentro do `DECISION SCOPE`, **sem exceção por severidade**. Rebaixar isso conforme severidade recriaria exatamente o loophole "não sabemos se quebrou, mas é LOW, então libera" — proibido. Um item pode ser tratado como informational apenas se estiver explicitamente marcado como `OUT OF DECISION SCOPE` ou comprovadamente não relacionado ao changeset avaliado — e essa determinação de escopo, quando ambígua, produz `INCONCLUSIVE` no próprio gate (não `BLOCKED` nem passagem silenciosa), porque nesse caso o problema é não saber se o item participa da decisão, não saber que ele falhou.

## Passo 4 — Verificação manual e verification contract

O critério não é automatizado-versus-manual. É:

```
A evidência apresentada satisfaz o verification contract
aplicável a esse invariante/item?
```

`MANUAL ≠ automaticamente fraco`. `AUTOMATED ≠ automaticamente suficiente`.

Verificação manual **satisfaz** o gate quando reúne todos estes elementos:

```
- método de verificação permitido/adequado para aquele invariante
  (definido em RECH_INVARIANTS.md quando existir um verification
  contract explícito para o item; na ausência dele, um método
  manual só é aceito se o comportamento for genuinamente não
  automatizável no estágio atual do projeto);
- procedimento reproduzível descrito;
- resultado esperado documentado;
- resultado observado documentado;
- evidência/artefato registrado, quando aplicável (screenshot,
  output, comparação estrutural).
```

Verificação manual **não satisfaz** o gate (→ hard blocker) quando:

- é vaga ("conferi e está ok", sem procedimento nem resultados registrados);
- o invariante é automatizável e o projeto já possui ou espera validação automatizada correspondente, mas ela foi omitida — checagem manual não compensa automação esperada e ausente, mesmo que a checagem manual em si esteja bem documentada.

## Passo 5 — Escopo da decisão e agregação de release

Para `DECISION UNIT: CHANGESET`, avalia-se exatamente o PR/branch/commit/diff/patch declarado — nada além disso, nada inferido sobre o resto do sistema.

Para `DECISION UNIT: RELEASE`, cada changeset constituinte precisa ter sido avaliado (por esta skill ou já ter um `RECH RELEASE GATE RESULT` anterior), e o veredito do release é agregado deterministicamente:

```
Se algum changeset = BLOCKED             → RELEASE = BLOCKED
senão, se algum changeset = INCONCLUSIVE → RELEASE = INCONCLUSIVE
senão, se algum changeset SEM avaliação  → RELEASE = BLOCKED
  (cobertura obrigatória faltando é falha de readiness, não incerteza)
senão                                     → RELEASE = READY
```

Nunca inferir aprovação global a partir de um subconjunto — um release com 9 changesets READY e 1 sem avaliação nenhuma é `BLOCKED`, não "provavelmente READY".

## Passo 6 — Relação com `rech-fix`

`STATUS: FIXED` da `rech-fix` não é prova de release-readiness — é evidência de que aquele problema específico foi corrigido corretamente (`LOCAL CORRECTNESS CHECK`), consumida como um insumo entre vários, nunca como autoridade final.

- **FIXED** → evidência positiva para o item específico; ainda depende do `regression-guardian` confirmar a superfície mais ampla antes de contribuir para `READY`.
- **PARTIALLY_FIXED** → cada item em `UNRESOLVED ISSUES` do relatório é avaliado individualmente contra o `DECISION SCOPE`: se tocar comportamento relevante ao changeset/release avaliado, vira hard blocker; se comprovadamente fora do escopo desta decisão, informational.
- **BLOCKED** (da rech-fix) → hard blocker direto — um fix que nunca completou não pode contribuir para `READY`.
- **INCONCLUSIVE** (da rech-fix) → hard blocker — comportamento esperado nunca foi estabelecido, sem base para autorizar avanço daquele item.

## Passo 7 — Evidência e completude

O gate não recalcula nem faz média do `CONFIDENCE` produzido pelas skills upstream — isso misturaria dois tipos diferentes de incerteza. Em vez disso, mantém um eixo próprio:

```
EVIDENCE COMPLETENESS: COMPLETE | PARTIAL | MISSING
```

— por campo obrigatório do input (Passo 0). O `CONFIDENCE` de cada item upstream é exposto no relatório sem ser alterado. Isso evita que confiança alta em alguns itens mascare a ausência de outro item obrigatório inteiro.

## Passo 8 — Output contract

Ver `references/gate-report-template.md` para o template completo. Estrutura mínima:

```
RECH RELEASE GATE RESULT

VERDICT: READY | BLOCKED | INCONCLUSIVE

DECISION UNIT: CHANGESET | RELEASE
SCOPE EVALUATED: <changeset específico, ou changesets constituintes do release>
EVIDENCE CONSUMED: <relatórios upstream usados>
EVIDENCE COMPLETENESS: <COMPLETE | PARTIAL | MISSING, por campo obrigatório>

HARD BLOCKERS: <lista, vazia se nenhum>
WARNINGS: <lista>
NON-BLOCKING FOLLOW-UPS: <lista, cada uma com ação e contexto>
INFORMATIONAL FINDINGS: <lista>

WHAT PASSED: ...
WHAT FAILED: ...
WHAT REMAINS UNRESOLVED: ...

JUSTIFICATION: <por que este veredito, referenciando as regras fixas aplicadas>
AUTHORIZED TO ADVANCE: <declaração precisa — ex. "merge do changeset X para main autorizado"; nunca "release autorizado" se o DECISION UNIT avaliado foi um CHANGESET isolado>
```

## Safeguards

- **Pressure-to-ship:** urgência de prazo nunca converte `BLOCKED` em `READY`. Se a pressão vier acompanhada de argumento genuíno para reclassificar um achado, isso segue o caminho normal de reavaliação de evidência — nunca um atalho de veredito.
- **Redefinição de blocker como warning/follow-up:** a lista de hard blockers (Passo 2) é fixa; classificação acontece antes do veredito ser computado, sem discricionariedade para amaciar.
- **Ignorar teste falho:** qualquer teste obrigatório falhando é hard blocker, sem exceção.
- **Liberar mudança com regressão conhecida:** `REGRESSION`, em qualquer severidade, é sempre hard blocker.
- **Escopo parcial representado como total:** `SCOPE EVALUATED` sempre explícito; regra de agregação do Passo 5 para `RELEASE`.
- **Ausência de evidência como evidência de ausência:** campo obrigatório ausente nunca é interpretado como "sem problemas" — é `BLOCKED` por definição (Passo 1), nunca `READY` por omissão.

## Referências

- `references/gate-report-template.md` — template consolidado do `RECH RELEASE GATE RESULT`.
- `references/acceptance-cases.md` — os 12 casos canônicos que validam esta skill, incluindo os marcados como HARD ACCEPTANCE.
