---
name: rech-regression-guardian
description: "Compara uma mudança candidata (branch, diff, refatoração, correção, migração) contra o baseline de comportamento já estabelecido de um projeto RECH, para detectar se algo previamente garantido deixou de funcionar. Classifica cada item como REGRESSION, CHANGE, PASS ou INCONCLUSIVE, com CONFIDENCE separada, e veredito global por precedência (REGRESSION acima de INCONCLUSIVE acima de CHANGE acima de PASS). Use antes de mergear ou promover mudança em código clínico do RECH, mesmo sem pedido explícito, e sempre depois de rech-fix (evidência upstream, não prova de ausência de regressão). Dispare ao pedir corrigir, refatorar, migrar, substituir, remover, reescrever, simplificar ou otimizar algo que já funciona; comparar versões/branches; validar release; perguntar se algo pode quebrar; comparar com versão anterior; revisar um PR; ou citar merge/commit em RechDocs, RechStudy, RechSupps, RechTrauma, RechShift. Diferente de rech-deep-audit: pergunta se a mudança destruiu algo garantido. Não decide bloqueio de release."
---

# RECH Regression Guardian

## A pergunta que esta skill responde

Existem duas perguntas parecidas, mas diferentes, no ecossistema RECH:

- **rech-deep-audit** pergunta: *"O sistema está correto, aqui e agora?"*
- **rech-regression-guardian** pergunta: *"Essa alteração fez algo anteriormente garantido deixar de funcionar?"*

Um projeto pode passar no regression guardian e ainda ter bugs antigos não relacionados à mudança atual. E pode melhorar a arquitetura, corrigir vinte bugs, e ainda assim introduzir uma regressão crítica em algo que não tinha nada a ver com o que estava sendo corrigido. São verificações independentes — não fundir uma na outra, e não rodar esta skill automaticamente dentro de toda chamada de auditoria geral. Ela roda quando existe uma **mudança concreta** (branch, diff, PR, refatoração) para comparar contra um **baseline concreto**.

Esta skill **detecta e classifica** regressões. Ela não decide se isso deve bloquear um merge ou release — essa decisão de gate pertence a uma etapa separada (hoje, ao Leandro; no futuro, possivelmente a uma `rech-release-gate` dedicada, que ainda não existe). Misturar detecção com decisão de bloqueio é o erro que este redesenho corrige.

O objetivo final não é burocratizar — é impedir a falha clássica de "o código atual faz assim, logo isso deve ser o comportamento correto", que destrói silenciosamente garantias clínicas (como as já documentadas em RAF: vazamento de parâmetro ventilatório pós-extubação, resolução silenciosa de estados conflitantes).

## Passo 0 — Input

```
REGRESSION REVIEW INPUT

CANDIDATE:
  branch | commit | diff | working tree | patch

BASELINE:
  explicit ref | stable version | inferred known-good baseline

EVALUATION SCOPE:
  files | components | capabilities | whole change-set

APPROVED BEHAVIOR CHANGES: (opcional)
  ...

UPSTREAM FIX REPORT: (opcional)
  RECH FIX RESULT de rech-fix, se esta mudança veio de lá

KNOWN INVARIANTS: (fornecidos ou descobertos durante a avaliação)
  ...

AVAILABLE BASELINE EVIDENCE: (descoberto durante a avaliação)
  ...
```

Só três campos são conceitualmente indispensáveis: **CANDIDATE**, **BASELINE**, **EVALUATION SCOPE**. Os demais são opcionais e enriquecem a análise quando disponíveis, mas a ausência deles não impede a execução.

Se o repositório estiver acessível (RechHub e os repos individuais em github.com), use `git diff BASE...CANDIDATE` para obter o diff real — ele não serve só para saber "o que mudou", mas para **direcionar quais invariantes e testes precisam ser verificados**. Não analise o repositório inteiro do zero a cada vez; use o diff para focar o escopo.

Se não for possível estabelecer um **BASELINE minimamente defensável** (nenhuma fonte da hierarquia do Passo 1 disponível, nem para inferência auxiliar), não invente um — o resultado correto é `INCONCLUSIVE`, não uma suposição otimista.

Nunca use um Personal Access Token colado na conversa; siga a governança já estabelecida no RechHub (PAT nunca em chat).

## Passo 1 — Baseline evidence hierarchy

Nem toda fonte de "comportamento esperado" tem o mesmo peso. Use esta ordem, do mais confiável ao menos confiável, e **sempre declare qual nível de evidência sustenta cada linha da matriz**:

```
BASELINE EVIDENCE HIERARCHY

1. FORMAL INVARIANT / EXPLICIT BEHAVIOR CONTRACT
2. VALIDATED GOLDEN CASE / FIXTURE
3. EXISTING AUTOMATED REGRESSION TEST
4. AUTHORITATIVE DOCUMENTED REQUIREMENT
5. KNOWN-GOOD GIT BASELINE + REPRODUCIBLE BEHAVIOR
6. DEMONSTRATED HISTORICAL BEHAVIOR
7. USER RECOLLECTION
```

1. **Invariante formal / contrato de comportamento explícito** — documentado em `RECH_INVARIANTS.md` (ver `references/invariants-format.md`). Aprovado pelo Leandro, maior confiança possível.
2. **Golden case / fixture validada** — fixtures em `tests/golden/` com input/output já validado manualmente como comportamento canônico. Fica acima do teste genérico porque um golden case explicitamente validado tende a representar o baseline mais diretamente; um teste qualquer pode estar obsoleto ou testar um detalhe incidental. Convenção desejada, **não presumida como existente** — verifique de fato se `tests/golden/` existe no repositório antes de citar este nível; onde não existir, declare `golden case: N/A — tests/golden/ não existe neste repo` e trate como vazio.
3. **Teste automatizado de regressão existente** — Vitest/Jest/Playwright/pytest/smoke tests. Evidência executável, mas não soberana: um teste pode estar obsoleto ou testar um detalhe incidental que já não reflete o requisito atual (ver a regra de recência abaixo).
4. **Requisito documentado autoritativo** — RECH_STATUS.md, AI_HANDOFF.md, ARCHITECTURE.md, SAFEGUARDS.md, ADRs, checklists de aceite (ex.: RECHSHIFT_CHECKLIST_ACEITE).
5. **Baseline git conhecido-bom + comportamento reproduzível** — o estado do main/release anterior, quando reproduzido e confirmado, não apenas assumido por estar em produção.
6. **Comportamento histórico demonstrado** — inspeção direta da versão anterior sem reprodução formal confirmada. Rotule como `DEMONSTRATED HISTORICAL BEHAVIOR — não confirmado como requisito`, porque comportamento antigo também pode ser bug.
7. **User recollection** — o Leandro relatando "antes funcionava assim" sem evidência documentada, testada ou reproduzível por trás. É evidência legítima, mas a mais fraca da hierarquia — sozinha, **nunca sustenta um veredito `REGRESSION`**, em nenhum nível de confiança. Sozinha, o máximo que sustenta é `INCONCLUSIVE` com `CONFIDENCE: LOW` — declarar `REGRESSION` a partir de recollection isolada, mesmo marcado como LOW, ainda seria apresentar como fato algo que não foi verificado.

### Inferência de código não é baseline formal

```
CODE INFERENCE ≠ ESTABLISHED BASELINE
```

Ler o código atual e concluir "é assim que deveria funcionar" não é um nível da hierarquia — código demonstra implementação, não demonstra que aquele comportamento era uma garantia a ser preservada. Inferência de código pode ser usada como evidência **auxiliar** para contextualizar uma linha da matriz, mas nunca sozinha para sustentar um veredito `REGRESSION`. Se não houver nada além de inferência de código, o item cai em `INCONCLUSIVE`, não em `REGRESSION`.

### A hierarquia não é absoluta no tempo

A hierarquia expressa força evidencial **padrão**, não uma licença para ignorar evidência mais nova e explicitamente aprovada. Um teste automatizado antigo (nível 3) não derrota automaticamente uma mudança de requisito aprovada depois dele — nesse caso, o teste está `stale` (desatualizado) e deve ser sinalizado como tal, sem que isso vire `REGRESSION` só porque o teste antigo ainda existe e falha. Ver Caso 5 em `references/acceptance-cases.md`.

## Passo 2 — Classificar o que está sob guarda

Para cada item avaliado, classifique em uma destas categorias (não misture):

- **INVARIANT** — contrato que nunca pode ser violado (ex.: `INV-RD-VENT-003`: parâmetros ventilatórios não podem vazar entre episódios pós-extubação). Violação = severidade CRITICAL por padrão.
- **CAPABILITY** — funcionalidade que deve continuar acessível, mas não é uma garantia clínica dura (ex.: upload múltiplo, preview, exportação, persistência offline).
- **SAFEGUARD** — mecanismo de proteção (validação, alerta, bloqueio de estado inconsistente) cuja ausência não quebra a função principal, mas remove uma rede de segurança.
- **KNOWN REGRESSION** — algo que já era um bug conhecido antes da mudança (não é uma regressão nova; não deve contaminar o veredito da mudança atual, mas deve ser registrado para não ser esquecido).

Três níveis de origem para os itens verificados:

- **A. Invariantes explícitos** — os mais importantes, precisam estar escritos em RECH_INVARIANTS.md. Se não existir esse arquivo para o projeto, ofereça criá-lo (ver `references/invariants-format.md`) em vez de manter tudo na cabeça do agente.
- **B. Invariantes descobertos** — ao analisar código/testes/SAFEGUARDS/findings RAF anteriores/commits/post-mortems, você pode encontrar um padrão que parece um invariante não documentado. Registre como `CANDIDATE INVARIANT` com a evidência que sustenta a suspeita e uma sugestão de promoção — mas **nunca promova sozinho**. Isso é uma sugestão para o Leandro decidir, não uma decisão automática.
- **C. Superfície funcional** — capacidades importantes que não são invariantes clínicos (upload, preview, layout, exportação, persistência). Entram como CAPABILITY.

## Passo 3 — Classificação por item

Para cada item relevante ao escopo do diff:

1. Determine o comportamento esperado (baseline) usando a hierarquia do Passo 1.
2. Determine o comportamento real no candidato — rode os testes existentes se possível (`npm test`/`vitest run` conforme o stack do projeto — vanilla JS/TS, Vitest/jsdom, sem React/Vite), ou inspecione o código/diff diretamente quando não houver teste executável.
3. Compare baseline vs candidato e atribua exatamente uma classificação:

```
CLASSIFICATION: REGRESSION | CHANGE | PASS | INCONCLUSIVE
```

- **REGRESSION** — comportamento previamente estabelecido foi quebrado, sem uma mudança de comportamento legitimamente aprovada por trás.
- **CHANGE** — o comportamento mudou, mas a mudança é intencional/explicitamente aprovada, ou existe uma mudança demonstrada sem base suficiente para chamá-la de regressão (ex.: teste antigo stale contradito por requisito posterior aprovado).
- **PASS** — nenhuma regressão foi demonstrada para o item avaliado, dentro do escopo avaliado.
- **INCONCLUSIVE** — a evidência disponível é insuficiente, conflitante, ou não confiável o bastante para estabelecer a classificação.

Nunca assuma sozinho que uma mudança é intencional — se não houver evidência explícita de aprovação (ex.: menção no PR, no AI_HANDOFF.md, ou confirmação do usuário na própria conversa), trate como candidata a `REGRESSION`, nunca como `CHANGE` por suposição.

Junto da classificação, registre dois atributos separados — eles não substituem a classificação, complementam:

```
CONFIDENCE: HIGH | MEDIUM | LOW
VERIFICATION: COMPLETE | LIMITED | MANUAL_REQUIRED
```

`CONFIDENCE` deriva do nível de evidência usado (Passo 1) — invariante formal sustenta HIGH; user recollection sozinha nunca sustenta mais que LOW. `VERIFICATION` descreve o quão automatizada foi a checagem: `COMPLETE` (teste automatizado rodou e confirmou), `LIMITED` (evidência parcial ou indireta), `MANUAL_REQUIRED` (precisa de inspeção humana antes de confiar no resultado). Isso evita usar `INCONCLUSIVE` como cesta genérica para tudo que precisa de revisão manual — um item pode ser `PASS` com `VERIFICATION: MANUAL_REQUIRED` (ex.: comportamento visual conferido por inspeção, não por teste automatizado, mas ainda assim confirmado como preservado).

`BLOCKED`, `PASS COM RESSALVAS` e `MANUAL REVIEW` não são mais estados válidos nesta skill — foram substituídos pelo par CLASSIFICATION + CONFIDENCE/VERIFICATION acima. Decisão de bloqueio de release não é responsabilidade desta skill.

## Passo 4 — Construir a matriz

Formato completo em `references/matrix-and-json-schema.md`. Estrutura mínima:

| ID | Área | Invariante/Funcionalidade | Baseline | Candidato | Evidência | Nível | Classification | Confidence | Verification |
|---|---|---|---|---|---|---|---|---|---|
| INV-RD-VENT-003 | Ventilação | Não propagar parâmetros após extubação | PASS | FAIL | teste + diff | 3 | REGRESSION | HIGH | COMPLETE |
| CAP-RD-UI-004 | Preview | Preview continua acessível | PASS | PASS | Playwright | 3 | PASS | HIGH | COMPLETE |
| REG-RD-012 | Upload | ≥10 anexos não quebra geração | PASS | PASS | golden case | 2 | PASS | HIGH | COMPLETE |

Sempre inclua uma seção separada, fora da tabela principal, para **mudanças aprovadas** (classificadas como `CHANGE`, nunca misturadas com `PASS`):

```
### Mudanças (CHANGE) — não são regressão

CHANGE-017 — Antitrombóticos removidos da interface
Baseline: presentes | Candidato: ausentes | Diff: SIM
CLASSIFICATION: CHANGE — mudança explicitamente aprovada (motivo: <razão>)
```

Isso é essencial: sem essa seção, `CHANGE` se perde dentro de `PASS` ou é mal classificado como `REGRESSION`, o que destrói a confiança na ferramenta rapidamente para os dois lados.

Produza a matriz sempre em Markdown (para leitura humana). Ofereça também a versão JSON estruturada (schema em `references/matrix-and-json-schema.md`) quando o usuário pedir algo que vá alimentar outra ferramenta, script, dashboard ou futura integração com CI/GitHub Actions — não gere o JSON por padrão se não for pedido, para não poluir a resposta.

## Passo 5 — Veredito global

O veredito global é derivado da classificação de todos os itens avaliados, por **precedência determinística** — não por contagem nem por severidade:

```
Se ≥1 item REGRESSION           → REGRESSION
senão, se ≥1 item INCONCLUSIVE  → INCONCLUSIVE
senão, se ≥1 item CHANGE        → CHANGE
senão                           → PASS
```

Ou seja: `REGRESSION > INCONCLUSIVE > CHANGE > PASS`. Um único item `REGRESSION`, mesmo de severidade LOW, torna o veredito global `REGRESSION` — a skill não pondera severidade para "amenizar" o veredito. Severidade continua sendo um atributo separado de cada item, relevante para quem for decidir o que fazer com o veredito, mas não sobrepõe a precedência acima.

```
REGRESSION VERDICT: REGRESSION

1 item REGRESSION detectado (severidade CRITICAL):
INV-RD-VENT-003 — parâmetros ventilatórios vazando entre episódios pós-extubação
CONFIDENCE: HIGH | VERIFICATION: COMPLETE

Esta skill não decide se isso bloqueia merge/release — essa decisão cabe
a você (ou, futuramente, a rech-release-gate). O que esta skill garante
é que a informação chegou até você antes da decisão ser tomada às cegas.
```

### Regra crítica sobre aprovação

Se o usuário disser "pode continuar" ou "aceito esse comportamento" diante de um item classificado `REGRESSION`, **isso não vira `PASS` automaticamente**. Isso deve gerar uma reclassificação explícita e visível, de `REGRESSION` para `CHANGE`:

```
REGRESSION
  ↓
CHANGE (aprovado por Leandro em <contexto/data>)
```

E sinalize que o invariante ou especificação correspondente em RECH_INVARIANTS.md/RECH_STATUS.md precisa ser **atualizado** para refletir o novo comportamento — senão a próxima execução da skill vai detectar a mesma coisa como `REGRESSION` de novo, e o histórico técnico fica incoerente com a realidade do sistema. Ofereça fazer essa atualização de documentação como parte do fechamento da tarefa, não deixe implícito.

## Composição com outras skills RECH

- **rech-deep-audit**: standalone, roda em paralelo, não em sequência automática. Pode ser útil rodar as duas quando uma mudança grande está sendo avaliada para release, mas cada uma produz seu próprio relatório com pergunta diferente — não fundir os relatórios em um só sem deixar claro qual seção responde qual pergunta.

- **rech-fix** (LOCKED, real, instalada): o fluxo típico é `rech-fix → rech-regression-guardian`, consumindo o `RECH FIX RESULT` como `UPSTREAM FIX REPORT` no input desta skill. Mas esta skill também pode ser executada sobre qualquer mudança concreta, com ou sem passagem prévia por `rech-fix`.

  A distinção de escopo entre as duas é formal e precisa ficar clara:

  ```
  rech-fix
  LOCAL CORRECTNESS CHECK
    — problema aprovado especificamente por aquele fix;
    — teste targeted daquele fix;
    — invariante diretamente vinculado ao fix (MUST LINK);
    — integridade daquele patch específico.

  rech-regression-guardian
  CHANGE-SURFACE REGRESSION CHECK
    — diff completo dentro do escopo avaliado;
    — outras capabilities potencialmente afetadas, além do que o fix visava;
    — todos os invariantes relevantes tocados pelo diff, não só o vinculado ao fix;
    — testes/golden cases de toda a superfície de mudança;
    — efeitos indiretos e comportamento baseline → candidate como um todo.
  ```

  ```
  RECH-FIX PASS/FIXED ≠ PROOF OF NO REGRESSION
  ```

  O `INVARIANT COMPLIANCE CHECK` que `rech-fix` executa cobre apenas o invariante que ela vinculou ao fix específico. Isso não substitui esta skill: o relatório da `rech-fix` é **evidência upstream** (pode virar uma linha de alta confiança na matriz, geralmente nível 3 se testado, ou nível 1 se o invariante coincidir), nunca autoridade final sobre ausência de regressão no restante do diff. Nunca confie em `STATUS: FIXED` da `rech-fix` como suficiente para pular a avaliação da superfície mais ampla do change-set.

- **Futura rech-release-gate**: esta skill não depende dela para funcionar, e não deve ser tratada como existente até estar de fato instalada. O veredito global desta skill (`REGRESSION`/`INCONCLUSIVE`/`CHANGE`/`PASS`) é a entrada que uma futura `rech-release-gate` consumiria para decidir bloqueio — mas essa decisão de bloqueio não é produzida aqui.

## Quando RECH_INVARIANTS.md não existe para o projeto

Não bloqueie a análise por isso — use os níveis 2–7 da hierarquia normalmente. Mas ao final do relatório, sinalize que a ausência desse arquivo reduz a confiança geral do sistema de guarda para esse projeto, e ofereça (sem insistir) começar a populá-lo com os invariantes que já ficaram evidentes durante a análise atual, usando o formato em `references/invariants-format.md`.

## Referências

- `references/invariants-format.md` — formato do RECH_INVARIANTS.md e convenção de IDs.
- `references/matrix-and-json-schema.md` — matriz Markdown completa e schema JSON, alinhados ao modelo CLASSIFICATION/CONFIDENCE/VERIFICATION.
- `references/acceptance-cases.md` — os 8 casos canônicos de regressão que validam esta skill, incluindo os 5 marcados como HARD ACCEPTANCE.
