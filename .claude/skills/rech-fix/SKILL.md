---
name: rech-fix
description: "Corrige um comportamento específico e já diagnosticado em um projeto RECH, com escopo controlado, causa raiz demonstrada e evidência antes/depois — nunca uma skill de 'melhorar código'. Use ao receber um finding de rech-deep-audit ou rech-regression-guardian, ou quando o usuário pedir para corrigir/consertar um bug específico em RechDocs, RechStudy, RechSupps, RechTrauma ou RechShift. Aplica o fluxo INPUT → INTAKE → REPRODUCE/VERIFY → ROOT CAUSE → CHECK INVARIANTS → DEFINE FIX SCOPE → PLAN → APPROVAL → CREATE/UPDATE TEST → IMPLEMENT FIX → LOCAL VERIFICATION → TEST SUITE → REGRESSION GUARDIAN → RELEASE GATE → REPORT. Dispare sempre que o pedido for consertar/corrigir/resolver um bug ou comportamento incorreto específico — NÃO dispare para refatoração exploratória, melhoria de performance sem bug relatado, ou pedidos vagos de 'deixar o código melhor' (isso foge do escopo desta skill, que exige um problema concreto e delimitado)."
---

# RECH Fix

## Regra central

`rech-fix` não é uma skill de melhorar código. É uma skill de corrigir **um** comportamento específico, aprovado, com escopo controlado e evidência antes/depois. Se não há um problema concreto e delimitado para corrigir, esta skill não é a ferramenta certa.

A regra que resume tudo: **FIX ONLY THE APPROVED PROBLEM.**

### Proibição absoluta: nunca alterar o requisito para o teste passar

`rech-fix` corrige o **código** para satisfazer o comportamento esperado — nunca o inverso. Se o teste está falhando e a correção parece difícil, a resposta nunca é afrouxar a asserção, redefinir o comportamento esperado, remover um caso de teste incômodo, ou ajustar o golden case para bater com o que o código atual produz, **sem que isso passe por um dos dois caminhos legítimos abaixo**. Fora deles, mudar o teste para fazê-lo passar não é um fix — é maquiar o sintoma no relatório em vez de resolvê-lo no sistema.

Existem exatamente dois cenários em que o teste (ou o requisito por trás dele) pode legitimamente mudar em vez do código:

**Cenário 1 — o requisito original nunca esteve certo**, descoberto durante a investigação:

```
REQUIREMENT QUESTIONED
Requisito original: ...
Motivo pelo qual parece incorreto: ...
Evidência: ...
```

Pare e volte para aprovação explícita — o requisito só muda por decisão humana, nunca porque "assim o teste passa".

**Cenário 2 — o comportamento aprovado mudou durante o processo.** O requisito original estava certo quando definido, mas uma decisão posterior (explícita, do Leandro) redefiniu o que é esperado. Isso é diferente de simplesmente *querer* que o teste passe — a mudança de comportamento precisa ser um pedido genuíno, não uma saída de conveniência sob pressão de prazo.

Quando o teste continua RED e existe pressão (do usuário ou de prazo) para simplesmente ajustar o teste, a resposta correta nunca é ceder silenciosamente. Se houver indício real de que o comportamento deveria mudar, sinalize o pedido primeiro, sem aplicar a mudança ainda:

```
APPROVED BEHAVIOR CHANGE REQUIRED
Comportamento antigo (o que o teste original verificava): ...
Comportamento novo solicitado: ...
Solicitado por: <contexto>
Status: aguardando aprovação explícita
```

Só depois que a aprovação de fato ocorrer — não pela pressão em si, mas por uma decisão explícita e deliberada — o teste é atualizado e o registro final passa a:

```
APPROVED BEHAVIOR CHANGE
Comportamento antigo (o que o teste original verificava): ...
Comportamento novo (aprovado): ...
Aprovado por: <contexto/data>
Teste atualizado: <nome/arquivo>
Invariante/spec correspondente atualizado: SIM/NÃO — <se NÃO, sinalizar pendência>
```

Se a aprovação não vier, ou vier apenas como insistência ("precisamos disso hoje") sem decisão deliberada sobre o comportamento em si, o resultado correto é `STATUS: BLOCKED` — nunca a edição do teste como atalho.

Este é o mesmo mecanismo que `rech-regression-guardian` usa para reclassificar regressão aparente como mudança aprovada. Se o invariante/spec correspondente não for atualizado junto, a próxima execução do regression guardian vai detectar isso como regressão de novo. Fora desses dois cenários, qualquer alteração de teste, asserção, comportamento esperado ou golden case sem uma dessas seções explícitas no relatório é a violação mais direta desta regra.

## O pipeline

```
INPUT
  ↓
INTAKE
  ↓
REPRODUCE / VERIFY
  ↓
ROOT CAUSE
  ↓
CHECK INVARIANTS
  ↓
DEFINE FIX SCOPE
  ↓
PLAN
  ↓
APPROVAL
  ↓
CREATE/UPDATE TEST
  ↓
IMPLEMENT FIX
  ↓
LOCAL VERIFICATION
  ↓
TEST SUITE
  ↓
RECH-REGRESSION-GUARDIAN
  ↓
RELEASE GATE
  ↓
REPORT
```

Cada etapa tem uma responsabilidade única — não pule etapas mesmo quando o bug parece óbvio; é exatamente nos casos "óbvios" que o INTAKE malfeito ou o ROOT CAUSE pulado causam fixes que resolvem o sintoma errado.

### INPUT

Dois caminhos de entrada possíveis:

**PATH A — Formal finding** (preferencial) — já vem estruturado de `rech-deep-audit`, `rech-regression-guardian`, um bug documentado, issue, ou finding RAF anterior:

```
finding_id
severity
evidence
affected_component
expected_behavior
observed_behavior
```

```
rech-deep-audit → approved finding → rech-fix
```

**PATH B — Pedido direto de correção** — algo como "o botão X deixou de funcionar", sem finding formal por trás:

```
pedido direto → minimal diagnosis → problem boundary established
  → approval se o escopo real divergir materialmente do relatado → rech-fix
```

Exigir uma auditoria profunda para um defeito perfeitamente delimitado burocratizaria demais o sistema — por isso PATH B existe. Mas isso não significa aceitar qualquer coisa como entrada: um pedido vago como **"melhore o RechDocs"** não é um finding, não tem fronteira de problema identificável, e não deve ser aceito por esta skill. Nesse caso, recuse educadamente e sugira o caminho apropriado (ex.: `rech-deep-audit` para levantar findings concretos primeiro).

### INTAKE

Se a entrada foi PATH A (finding formal), confirme que os campos obrigatórios estão presentes e siga para REPRODUCE/VERIFY. Se foi PATH B (pedido direto), esta etapa é o **minimal diagnosis** que estabelece a fronteira do problema antes de tocar em código:

```
FIX INTAKE
Problema relatado: ...
Comportamento observado: ...
Comportamento esperado: ...
Escopo afetado: ...
Evidência disponível: ...
Risco estimado: ...

PROBLEM BOUNDARY: <descrição delimitada do que está e não está incluído>
```

Se, ao investigar, o escopo real do problema se mostrar **materialmente maior ou diferente** do que foi relatado inicialmente (ex.: "botão não funciona" revela um problema estrutural em vários componentes, não um bug isolado), pare imediatamente, antes de aplicar qualquer alteração material, e declare:

```
SCOPE EXPANSION DETECTED
Escopo original: ...
Escopo real descoberto: ...
Evidência: ...
```

Novo conhecimento sobre a causa **não implica automaticamente nova autorização** para modificar o sistema — o escopo original que motivou PATH B (sem auditoria formal) não vale mais para o escopo real descoberto. Peça aprovação explícita do novo escopo antes de prosseguir para ROOT CAUSE ou qualquer etapa seguinte.

Se não for possível determinar o **comportamento esperado** com confiança suficiente, pare aqui — não avance tentando adivinhar corrigindo até "parecer certo":

```
STATUS: INCONCLUSIVE
Motivo: <o que falta para prosseguir>
```

e peça a definição ou evidência que falta. Isso impede o anti-pattern mais perigoso desta categoria: mudar código até o sintoma sumir sem nunca ter confirmado o que era, de fato, correto.

### REPRODUCE / VERIFY

Confirme que o bug existe de fato antes de investigar a causa — um finding pode estar desatualizado, mal descrito, ou já ter sido corrigido em outro commit. Reproduza o comportamento observado (execução real, teste que falha, ou inspeção direta do código que comprova a condição). Declare de onde vem esse entendimento do estado atual, na mesma lógica de hierarquia de evidência de `rech-regression-guardian` (invariante > spec > golden case > teste > estado do main > observado > inferência):

```
BASELINE STATE: <main / teste existente / release anterior / spec / reprodução manual>
```

Se não for possível confirmar nenhuma dessas fontes:

```
BASELINE: UNVERIFIED
```

Um fix aplicado sem baseline claro é um fix que ninguém consegue validar depois se resolveu o problema certo. Se a reprodução falhar (o bug não se manifesta como descrito), pare e reporte — não prossiga como se o bug fosse confirmado.

### ROOT CAUSE

Não corrija apenas o sintoma quando houver evidência suficiente para localizar a causa:

```
SYMPTOM: <o que foi observado>
IMMEDIATE CAUSE: <o que dispara o sintoma diretamente>
ROOT CAUSE: <por que essa condição existe no sistema>
FIX TARGET: <onde a correção deve efetivamente atuar>
```

Se a causa raiz não puder ser demonstrada com a evidência disponível, não finja certeza:

```
ROOT CAUSE CONFIDENCE: LOW
```

### CHECK INVARIANTS

Antes de definir o escopo do fix, verifique se o comportamento envolvido corresponde a um invariante já documentado em `RECH_INVARIANTS.md`. Isso é feito cedo no pipeline porque **informa a severidade e se a aprovação é obrigatória** — um fix que toca um invariante CRITICAL não pode ser tratado com a mesma leveza de um bug isolado sem invariante associado.

```
Invariante relacionado encontrado: <INV-XX-YYY-NNN> | nenhum
```

Se existir, referencie o ID e carregue sua severidade para as etapas seguintes — o vínculo é obrigatório, não opcional:

```
FIX
 └── MUST LINK → invariante existente
```

Se **não existir** invariante formal para esse comportamento, mas o bug revelar uma propriedade que deveria permanecer verdadeira, registre um candidato — nunca invente ou promova sozinho uma nova regra arquitetural, essa decisão é sempre do Leandro:

```
CANDIDATE INVARIANT DETECTED
Candidate: "<descrição do contrato implícito revelado pelo bug>"
Evidence:
- finding/bug atual
- <outra evidência relacionada, se houver>
- affected component <componente>
Recommendation: Consider promoting to formal invariant.
```

### DEFINE FIX SCOPE

Delimite, antes de planejar a implementação, o **patch budget**: o menor conjunto coerente de alterações capaz de resolver a causa raiz sem degradar a arquitetura.

```
MINIMAL ≠ menor número possível de caracteres/linhas
MINIMAL = menor mudança coerente que resolve a causa raiz
          sem degradar a arquitetura
```

Isso evita os dois extremos: um patch cosmético que só mascara o problema, e uma refatoração de meio projeto para corrigir um botão.

Classifique toda mudança candidata em uma destas quatro categorias — só as duas primeiras entram no patch:

| Categoria | Entra no patch? | Critério |
|---|---|---|
| **REQUIRED CHANGE** | Sim | A mudança que resolve diretamente a causa raiz identificada. |
| **NECESSARY SUPPORTING CHANGE** | Sim, se demonstrável | Não é a correção em si, mas é indispensável para que a correção funcione (ex.: ajustar assinatura de função usada em outro ponto, atualizar tipo compartilhado). Exige justificativa explícita de por que é necessária, não só conveniente. |
| **ADJACENT IMPROVEMENT** | Não | Melhoria relacionada à área tocada, mas não necessária para o fix (ex.: refatorar função vizinha, corrigir nome de variável). |
| **UNRELATED IMPROVEMENT** | Não | Qualquer coisa notada durante o trabalho sem relação direta com o fix (ex.: outro bug encontrado, dependência desatualizada, CSS inconsistente em outra tela). |

Tudo que não for REQUIRED ou NECESSARY SUPPORTING vai para uma lista separada, nunca entra silenciosamente no patch:

```
ADJACENT_FINDINGS:
- <achado> — <por que não entra neste fix>
```

### PLAN

Consolide o diagnóstico e o plano de correção em um pacote apresentável para aprovação:

```
DIAGNÓSTICO: ...
CAUSA: ...
FIX PROPOSTO: ...
ARQUIVOS AFETADOS: ...
RISCO: ...
TESTES A CRIAR/ALTERAR: ...
IMPACTO ESPERADO: ...
```

### APPROVAL

Espere autorização explícita antes de criar o teste ou tocar em código quando o fix:

- muda comportamento observável;
- mexe em área crítica (clínica, financeira, de segurança);
- tem impacto HIGH ou CRITICAL (inclusive por herdar severidade de um invariante identificado em CHECK INVARIANTS);
- exige mudança arquitetural;
- modifica um contrato, invariante ou spec já documentado;
- envolve múltiplos componentes.

Padrão no ecossistema RECH: pedir aprovação sempre, mesmo para correções que parecem óbvias. Pular esta etapa só é aceitável quando **todas** as condições em `references/decision-gates.md` forem verdadeiras — e mesmo assim o relatório completo continua obrigatório, só a pausa para autorização é que muda.

`APPROVE FIX ≠ APPROVE RELEASE` — esta aprovação autoriza que o diagnóstico está certo e o plano pode prosseguir. Não é a mesma decisão que aprovar a promoção para produção, que só acontece depois de REGRESSION GUARDIAN e RELEASE GATE.

### CREATE/UPDATE TEST

Depois de aprovado, e **antes** de implementar o fix, crie ou atualize o teste que vai comprovar o bug e sua correção — não basta rodar os testes existentes, porque se o bug passou por eles, havia um buraco na cobertura exatamente ali.

```
BUG REPRODUCIBLE + AUTOMATABLE
        │
        ▼
deve existir teste que falha antes (RED)
        │
        ▼
aplicar fix
        │
        ▼
mesmo teste passa depois (GREEN)
```

Exceção explícita para quando teste automatizado é inviável (comportamentos puramente visuais, dependentes de ambiente, ou sem infraestrutura adequada) — ver árvore de decisão completa em `references/decision-gates.md`:

```
TESTABILITY: LIMITED
AUTOMATED REGRESSION TEST: NOT AVAILABLE
REASON: <por que não foi possível automatizar>
ALTERNATIVE VERIFICATION: <evidência manual estruturada usada no lugar>
```

Nunca finja que houve teste automatizado quando a evidência foi manual — a distinção precisa ficar visível no relatório. E nunca escreva o teste já ajustado para o comportamento atual (errado) do código — o teste precisa falhar (RED) contra o código não corrigido, comprovando que ele de fato captura o bug.

### IMPLEMENT FIX

Aplique exatamente o fix definido em DEFINE FIX SCOPE e detalhado em PLAN — nada além disso. Se durante a implementação surgir a necessidade de tocar em algo fora do escopo aprovado, pare e volte para PLAN/APPROVAL com o escopo revisado, em vez de expandir silenciosamente.

### LOCAL VERIFICATION

Confirme que o teste criado em CREATE/UPDATE TEST agora passa (GREEN) contra o código corrigido.

Se o teste **continuar falhando** depois do fix aplicado, o fix está incompleto ou incorreto — corrija o código, não o teste. As únicas saídas que não sejam voltar e corrigir o código são os dois cenários já descritos na Proibição Absoluta: `REQUIREMENT QUESTIONED` (o requisito nunca esteve certo) ou `APPROVED BEHAVIOR CHANGE REQUIRED` seguido de aprovação explícita (o comportamento deveria mudar por decisão do Leandro) — ambos exigem parar e registrar a seção correspondente, nunca uma edição silenciosa do teste. Se nenhum dos dois cenários se aplica e o teste continua RED após tentativas razoáveis de correção, o resultado é:

```
STATUS: BLOCKED
Motivo: teste RED persistente sem correção legítima disponível dentro do escopo aprovado
```

— nunca ceder e afrouxar o teste só porque há pressão de prazo ou de terceiros.

**Teste verde não é suficiente por si só.** Mesmo com o teste específico passando (GREEN), verifique explicitamente se o fix viola o invariante vinculado em CHECK INVARIANTS:

```
INVARIANT COMPLIANCE CHECK
Invariante vinculado: <INV-XX-YYY-NNN | nenhum>
Fix viola o invariante?: SIM/NÃO
```

Se a resposta for SIM, **a solução candidata é rejeitada mesmo com o teste específico verde** — teste local passando não supera violação de invariante. Volte para IMPLEMENT FIX e busque uma correção compatível com o invariante, ou retorne `STATUS: BLOCKED` se nenhuma solução compatível for encontrada dentro do escopo aprovado. Nunca declare `STATUS: FIXED` nessa condição.

### TEST SUITE

Rode a suíte relacionada ao componente e, em seguida, a suíte completa adequada ao projeto. Registre os resultados de ambas — passar só na suíte relacionada não é suficiente para fechar esta etapa.

### RECH-REGRESSION-GUARDIAN

Entregue o pacote completo (diagnóstico, fix, teste, resultados de suíte) para `rech-regression-guardian` confirmar que nada mais quebrou. `rech-fix` não pula esta etapa mesmo quando o fix parece isolado — é exatamente a suposição de "isso não afeta mais nada" que a etapa existe para verificar.

### RELEASE GATE

Resultado técnico da checagem de regressão, não uma aprovação humana disfarçada:

```
RELEASE GATE: READY
```

ou bloqueado, conforme o veredito do regression guardian. A decisão de fato de mergear/promover continua sendo do Leandro.

Nota: hoje este veredito técnico é produzido a partir do resultado de `rech-regression-guardian`. Se no futuro existir uma skill dedicada `rech-release-gate`, esta etapa passaria a delegar a ela — mas não pressuponha que essa skill já existe até que esteja de fato instalada no ambiente.

### REPORT

O contrato de saída final é sempre este, independente de quão simples o fix pareceu — os campos são fixos, mas o conteúdo se adapta ao `STATUS`:

```
RECH FIX RESULT

STATUS: FIXED | PARTIALLY_FIXED | BLOCKED | INCONCLUSIVE

APPROVED PROBLEM: <o problema que foi de fato aprovado para correção>
PROBLEM BOUNDARY: <o que está e não está incluído no escopo aprovado>
ROOT CAUSE: ...
EVIDENCE BEFORE: ...
CHANGE APPLIED: ...
FILES CHANGED: ...
WHY EACH CHANGE WAS NECESSARY: ...
CHANGE CLASSIFICATION: <REQUIRED CHANGE / NECESSARY SUPPORTING CHANGE por arquivo/trecho, de DEFINE FIX SCOPE>
TEST ADDED/UPDATED: ...
TESTABILITY: FULL | LIMITED
TEST / EVIDENCE BEFORE: <RED do teste automatizado, ou evidência manual antes, se LIMITED>
TEST / EVIDENCE AFTER: <GREEN do teste automatizado, ou evidência manual depois, se LIMITED>
RELATED INVARIANT: <ID, se houver vínculo MUST LINK>
CANDIDATE INVARIANT: <descrição, se detectado e não promovido>
REGRESSION RISKS: ...
ADJACENT FINDINGS: ...
UNRESOLVED ISSUES: ...
NEXT REQUIRED STEP: rech-regression-guardian
```

`RELATED INVARIANT` e `CANDIDATE INVARIANT` são campos distintos — um fix pode ter um sem o outro, ou nenhum dos dois, mas nunca preencha um genérico "invariante" fundindo os dois conceitos: um é vínculo confirmado, o outro é sugestão não promovida.

**`STATUS: FIXED` não significa "pronto para merge".** Isso é responsabilidade das etapas seguintes (REGRESSION GUARDIAN → RELEASE GATE) e, no fim, da decisão humana. Esta separação é importante — não deixe a palavra "FIXED" carregar mais peso do que ela deveria: ela descreve o resultado técnico do fix em si, não uma autorização de deploy.

Estados de `STATUS`:
- **FIXED** — causa raiz corrigida, teste RED→GREEN confirmado (ou evidência alternativa estruturada quando `TESTABILITY: LIMITED`), e sem violação de invariante detectada em LOCAL VERIFICATION.
- **PARTIALLY_FIXED** — parte do problema foi resolvida, mas algo identificado em `UNRESOLVED ISSUES` permanece (ex.: causa raiz tem dois mecanismos, só um foi corrigível dentro do escopo aprovado — o outro fica documentado com o motivo e a próxima ação necessária).
- **BLOCKED** — não foi possível prosseguir: aprovação pendente, `SCOPE EXPANSION DETECTED` sem nova aprovação, teste RED persistente sem correção legítima disponível, solução candidata rejeitada por violar invariante sem alternativa encontrada, ou dependência externa.
- **INCONCLUSIVE** — não foi possível determinar comportamento esperado ou causa raiz com confiança suficiente para agir (inclusive quando fontes de evidência entram em conflito entre si — código, teste antigo, documentação e histórico git dizendo coisas diferentes). Nesse caso, `EVIDENCE BEFORE` documenta o conflito encontrado, `CHANGE APPLIED` fica vazio, e `NEXT REQUIRED STEP` aponta a decisão humana necessária para estabelecer o comportamento esperado — a skill nunca escolhe arbitrariamente qual fonte "parece mais certa".

Ver `references/fix-report-template.md` para o template consolidado com todas as seções do pipeline em ordem, pronto para colar em um PR ou no AI_HANDOFF.md do projeto. Ver `references/acceptance-cases.md` para os 8 casos canônicos que validam esta skill, incluindo os 5 marcados como HARD ACCEPTANCE.

## Referências

- `references/fix-report-template.md` — template consolidado do relatório, seguindo a ordem do pipeline.
- `references/decision-gates.md` — critérios detalhados para pular a etapa APPROVAL em casos triviais, e a árvore de decisão completa de TESTABILITY.
- `references/acceptance-cases.md` — os 8 casos canônicos (incluindo casos adversariais) que servem como acceptance criteria verificáveis para esta skill. 5 deles são HARD ACCEPTANCE: falhar em qualquer um invalida a skill inteira, independente do desempenho nos demais.
