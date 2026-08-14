---
name: rech-repo-context
description: "Estabelece o estado factual, atual e verificável de um repositório RECH relevante para uma tarefa, antes que outra skill (rech-fix, rech-regression-guardian, rech-release-gate, rech-deep-audit) tome decisões sobre ele. Não audita qualidade, não corrige código, não decide regressão nem release — só reporta ground truth: branch/HEAD/working tree reais, arquitetura como mapa, invariantes conhecidos, separando FACT de INFERENCE e CURRENT de HISTORICAL/PLANNED STATE. Estritamente read-only: nunca escreve no repositório, nunca executa código do projeto (testes, build, scripts, chamadas de API) — só introspecção (git status/diff/log, leitura de arquivos, parsing estático). Use antes de rech-deep-audit ou rech-fix sobre repositório/área sem contexto recente, ao trocar de projeto, quando branch ou working tree mudaram, ou quando o usuário disser 'continua de onde paramos' após tempo ou mudanças possíveis. Nunca trata memória de conversa, doc desatualizada, ou proposta futura como estado atual."
---

# RECH Repo Context

## Missão

**"Qual é o estado real, atual e verificável deste repositório, relevante para a tarefa que será executada?"**

Estabelece **ground truth operacional**. Não é auditoria (não julga se o sistema está correto), não corrige, não recomenda arquitetura, não decide regressão nem release. Esta é a skill de entrada da esteira RECH — se ela construir contexto errado, todas as decisões posteriores (fix, regressão, release) herdam essa falha silenciosamente. Por isso o rigor aqui é mais alto, não mais baixo, que o das outras skills: um erro de contexto não falha visivelmente, ele contamina.

## Fronteira de execução (READ-ONLY, sem exceção)

Esta skill nunca escreve no repositório — nenhum commit, nenhuma criação/atualização de arquivo (incluindo `REPO_CONTEXT.md`, `AI_HANDOFF.md`, `RECH_STATUS.md` ou qualquer outro), nenhuma mudança de branch/estado Git.

**Introspecção read-only permitida:**
```
git status
git rev-parse
git branch
git diff / git diff --stat
git log
leitura/listagem de filesystem
parsing estático de código/config/package/CI
```

**Nunca executa código do projeto:**
```
test suites (npm test, vitest, pytest, ...)
build (npm run build, ...)
startup da aplicação (npm start, node app.js, ...)
scripts do próprio projeto
migrations
chamadas de API (inclusive as chamadas client-side multi-provedor de IA
  já presentes em vários projetos RECH — rodar suíte "só para descobrir
  estado" teria custo e efeito colateral reais, não é uma ação neutra)
browser/E2E
qualquer comando com efeito colateral potencial
```

Se um fato só pode ser determinado executando o software:

```
RUNTIME STATUS: NOT VERIFIED
```

E, se esse fato for material ao `TASK SCOPE` da tarefa atual:

```
CONTEXT STATUS: PARTIAL
```

Nunca execute a aplicação, testes, ou qualquer script do projeto apenas para transformar `PARTIAL` em `CURRENT` — a fronteira read-only vale mesmo quando isso deixa o contexto incompleto. Incompletude declarada é sempre preferível a completude obtida violando o boundary.

## Passo 0 — Unidade de contexto e input

```
UNIT OF CONTEXT = REPOSITORY + REF/BRANCH + WORKING TREE STATE + TASK SCOPE + SNAPSHOT MOMENT
```

Um snapshot vale exatamente para essa combinação. Se qualquer dimensão mudar, o snapshot não é mais reaproveitável automaticamente para a dimensão que mudou.

```
REPO CONTEXT INPUT

REPOSITORY: <obrigatório>
TARGET REF / BRANCH: <obrigatório — default: HEAD atual se não especificado>
TASK / INTENT: <obrigatório — sem isso não há como decidir o que é "relevante">
EVALUATION SCOPE: <opcional — restringe a módulos/arquivos específicos>
PRIOR CONTEXT SNAPSHOT: <opcional — fornecido externamente: output anterior,
  contexto de sessão, artefato externo, ou outro mecanismo de persistência
  que não seja a própria skill>
USER-SUPPLIED CONSTRAINTS: <opcional>
```

`TASK / INTENT` é obrigatório: sem uma tarefa declarada, a skill não tem base para decidir o que é relevante, e viraria uma auditoria completa do repositório — que não é seu papel.

**Checagem cruzada de escopo:** compare o que `TASK / INTENT` sugere ser necessário contra o `EVALUATION SCOPE` efetivamente declarado. Se a tarefa aparentar tocar algo fora do escopo coberto (ex.: escopo declarado cobre só um módulo, mas a tarefa descrita na conversa menciona outro), sinalize essa lacuna explicitamente no output — nunca deixe o `EVALUATION SCOPE` reportado de forma passiva quando há indício de que ele está incompleto para a tarefa real.

`PRIOR CONTEXT SNAPSHOT`, quando fornecido, nunca vem de um arquivo que a própria skill escreveu — ela não persiste nada (ver fronteira de execução acima). É sempre insumo externo.

## Passo 1 — Snapshot ID, Snapshot Time e State Fingerprint

Três conceitos distintos, nunca fundidos:

```
SNAPSHOT ID       — identificador único desta observação específica
SNAPSHOT TIME     — instante em que a observação foi feita
STATE FINGERPRINT — identidade do estado factual relevante observado,
                     SEM componente de tempo
```

`STATE FINGERPRINT` deriva de:

```
repository identity + ref/branch + HEAD + working-tree fingerprint
  + task/evaluation-scope fingerprint
```

Dois snapshots tirados em momentos diferentes, sem nenhuma mudança material no repositório, têm `SNAPSHOT ID`/`SNAPSHOT TIME` diferentes, mas o **mesmo** `STATE FINGERPRINT`. Staleness (Passo 6) é determinada pelo `STATE FINGERPRINT`, nunca pela simples passagem de tempo entre observações — comparar dois snapshots e ver IDs diferentes não é, por si só, evidência de que algo mudou.

## Passo 2 — Sources of truth: duas categorias de fato

`repo-context` não julga o que deveria ser verdade — só relata o que é. Duas categorias, não uma hierarquia única:

```
FATOS SOBRE IMPLEMENTAÇÃO (o que de fato executa/existe agora)
  autoridade: git state + arquivos de código reais + config real
  ex.: "o código atual faz X" — verificável lendo o arquivo

FATOS SOBRE INTENÇÃO/CONTRATO DECLARADO (o que deveria acontecer)
  autoridade: RECH_INVARIANTS.md, ADRs, specs formais
  ex.: "o invariante declara que deveria ser Y" — verificável lendo o doc
```

Quando as duas categorias divergem — código faz X, invariante/doc declara Y — isso **não é resolvido** por esta skill. Vira uma entrada em `CONFLICTING EVIDENCE`, reportando os dois fatos lado a lado, cada um com sua fonte, deixando a decisão (é regressão? é intencional?) para quem consome o contexto — tipicamente `rech-regression-guardian`.

Ordem de confiabilidade **dentro** de cada categoria (não entre elas):
- Implementação: git state > arquivos reais inspecionados diretamente > config/package files > scripts (existência, não comportamento — nunca executados, ver fronteira acima).
- Intenção declarada: `RECH_INVARIANTS.md`/ADRs formais > `RECH_STATUS.md`/`AI_HANDOFF.md` > README > comentários no código > issues/PR text.

Conversa/memória e user recollection nunca entram como fato de estado atual do repositório — no máximo como contexto histórico ou `USER-SUPPLIED CONSTRAINTS`, nunca como `CURRENT FACT`.

## Passo 3 — Working tree tem precedência sobre HEAD para conteúdo observado

Distinção formal, sempre explícita no relatório:

```
COMMITTED STATE        = HEAD / ref selecionada
OBSERVED CURRENT CONTENT = working tree real
```

Quando a working tree está dirty (staged/unstaged/untracked relevantes), `CURRENT FACTS` sobre conteúdo de código/config devem refletir o que está de fato nos arquivos da working tree — **não** o que está em HEAD. `HEAD` continua registrado como referência committed/baseline, mas nunca substitui silenciosamente uma modificação local relevante. As duas realidades (committed vs observado) aparecem sempre lado a lado quando divergem — nunca só uma delas.

## Passo 4 — Current vs historical vs planned

```
CURRENT FACT     — verificado contra o estado presente (git/working tree)
                    no momento do snapshot
HISTORICAL FACT  — foi verdade em algum ponto passado (git log, changelog,
                    doc antiga); não confirmado como ainda verdadeiro; sempre
                    rotulado com a referência temporal
PLANNED STATE    — aparece em proposta/roadmap/TODO/RFC; não implementado;
                    nunca confundido com CURRENT, mesmo que a proposta seja
                    detalhada ou pareça iminente
DEPRECATED STATE — formalmente marcado como retirado/em retirada
UNKNOWN          — genuinamente não determinável a partir das fontes
                    disponíveis; nunca preenchido por suposição
```

Histórico Git explica *por que* o estado atual é o que é, mas nunca substitui a inspeção direta do estado atual.

## Passo 5 — Fact vs inference

```
FACT      — diretamente sustentado por evidência inspecionada
INFERENCE — conclusão derivada de fatos, mas não afirmada explicitamente
            por nenhuma fonte
```

Toda inferência material — que poderia mudar a decisão de uma skill consumidora — é rotulada `INFERENCE`, citando o(s) fato(s) de onde foi derivada. Nunca promovida a `FACT` por parecer óbvia. Este é o safeguard mais fácil de violar sob a pressão de "dar uma resposta completa" — resistir a essa pressão é o próprio ponto desta skill.

## Passo 6 — Staleness

```
CONTEXT STATUS: CURRENT | STALE | PARTIAL | INCONCLUSIVE
```

- **CURRENT** — `STATE FINGERPRINT` do snapshot bate com o estado presente.
- **STALE** — o `STATE FINGERPRINT` mudou desde o `PRIOR CONTEXT SNAPSHOT` fornecido (HEAD mudou, branch mudou, working tree mudou, dependências mudaram, merge/rebase ocorreu, escopo da tarefa mudou materialmente).
- **PARTIAL** — o que foi estabelecido continua válido para o que cobriu, mas não cobre o `EVALUATION SCOPE` da tarefa atual — inclusive quando a lacuna vem de um fato que só seria verificável executando código (ver fronteira de execução).
- **INCONCLUSIVE** — não dá para determinar se o snapshot anterior ainda é válido (ex.: HEAD destacado sem referência clara, estado Git ambíguo).

**Resistência a atalho adversarial:** se o usuário pedir para pular a verificação ("não precisa checar de novo, assume que está como da última vez, só segue"), a skill não produz `CONTEXT STATUS: CURRENT` nem `CURRENT FACTS` não verificados só para atender ao pedido de agilidade. Sem `PRIOR CONTEXT SNAPSHOT` válido (ou com um claramente desatualizado), o resultado correto é `PARTIAL` ou `INCONCLUSIVE`, com tudo que não foi checado rotulado `INFERENCE`/`UNKNOWN` — nunca `FACT` por conveniência. Pressão para agilizar não é evidência de que o estado não mudou.

## Passo 7 — Constraint model

Mesma taxonomia usada no design de `rech-github-scout`, mantendo linguagem consistente no ecossistema. Aqui a skill **descobre e registra**, nunca cria:

- **HARD CONSTRAINT** — só com evidência textual explícita (doc formal, ADR) ou ausência estrutural inequívoca observada diretamente (ex.: sem bundler configurado nos arquivos de build).
- **PREFERRED** — preferência declarada explicitamente em doc de governança.
- **CURRENT CONSTRAINT** — limitação descritiva do estado atual, sem ser regra deliberada; pode mudar sem violar nada.

Ausência observada, sem doc explícito, é sempre `CURRENT CONSTRAINT` por default — nunca `HARD` só por inferência.

## Passo 8 — Architecture, test e git snapshot

**Architecture snapshot** — mapa, não avaliação: runtime/plataforma, linguagem, framework (ou ausência), entry points, módulos principais, storage/estado, integrações externas, build, sistema de teste, modelo de deploy. Substantivos e estrutura, nunca adjetivos de qualidade.

**Test/validation snapshot** — descobre comandos, suítes existentes, configuração de CI; nunca executa (ver fronteira de execução). Se o status de execução de algo for necessário e não puder ser obtido sem rodar código, `RUNTIME STATUS: NOT VERIFIED`.

**Git snapshot** — repository, branch/ref atual, HEAD, working tree clean/dirty (com staged/unstaged/untracked relevantes discriminados), relação com branch padrão (ahead/behind).

**Checagem de branch/ref antes de qualquer outro fato:** compare o `TARGET REF/BRANCH` declarado no input contra o que foi de fato observado no repositório. Se divergirem (ex.: input pede `feature/x`, mas o checkout real está em `main`), sinalize essa discrepância de forma explícita e proeminente **antes** de reportar qualquer outro fato — todo fato subsequente estaria implicitamente associado ao contexto errado se essa checagem for pulada.

## Passo 9 — Integração com outras skills (v1: sem invocação automática)

Nesta v1, nenhuma skill chama `rech-repo-context` automaticamente, e ela não chama nenhuma outra — a orquestração dessa decisão é responsabilidade de quem está conduzindo a tarefa (o Leandro, ou uma camada de orquestração futura), não desta skill nem das já `LOCKED`. `rech-repo-context` apenas sinaliza sua própria relevância:

```
REQUIRED     — repositório/área sem contexto CURRENT E a tarefa tem
               escopo não-trivial (multi-componente, arquitetural, ou
               severidade HIGH/CRITICAL já indicada).
RECOMMENDED  — área não tocada recentemente na sessão, ou ambiguidade
               estrutural que repo-context resolveria com mais confiança.
NOT NEEDED   — tarefa trivial e delimitada, em área já coberta por
               snapshot CURRENT.
```

Fronteiras com as skills já `LOCKED` (nenhuma delas foi ou será alterada por esta skill):

- **rech-deep-audit**: `repo-context` responde "o que existe e qual é o estado atual?"; `deep-audit` responde "há problemas e o sistema está correto?". `repo-context` nunca produz findings de qualidade — no máximo aponta uma observação não avaliada, sugerindo `deep-audit` como próximo passo.
- **rech-fix**: pode alimentar o `INTAKE`/`REPRODUCE-VERIFY` com arquitetura, constraints e localização de invariantes já mapeados, mas `rech-fix` continua livre para rodar sem `repo-context` em casos triviais delimitados.
- **rech-regression-guardian**: pode alimentar `EVALUATION SCOPE`/`KNOWN INVARIANTS` do input do guardian; nunca antecipa `REGRESSION`/`CHANGE`/`PASS`/`INCONCLUSIVE`.
- **rech-release-gate**: pode estabelecer identidade/escopo do changeset; nunca produz `READY`/`BLOCKED`/`INCONCLUSIVE`.

## Output contract

```
RECH REPO CONTEXT

SNAPSHOT ID: ...
SNAPSHOT TIME: ...
STATE FINGERPRINT: <repo + ref + HEAD + working-tree fingerprint + task/scope fingerprint, sem tempo>

REPOSITORY: ...
REF / BRANCH: ...
COMMITTED STATE (HEAD): ...
OBSERVED CURRENT CONTENT (working tree): <clean | dirty — com staged/unstaged/untracked discriminados>

TASK: ...
EVALUATION SCOPE: ...

CURRENT ARCHITECTURE: <mapa>
ENTRY POINTS: ...
IMPORTANT MODULES: ...
STORAGE / STATE: ...
BUILD: ...
TESTS: <comandos/suítes descobertos — RUNTIME STATUS: NOT VERIFIED quando aplicável>
CI: ...

INVARIANTS / CONTRACTS: <localização>
HARD CONSTRAINTS: ...
PREFERENCES: ...
CURRENT CONSTRAINTS: ...

CURRENT FACTS (implementação): ...
DECLARED INTENT FACTS (contrato/invariante): ...
MATERIAL INFERENCES: <rotuladas como tal, com fato-base citado>
HISTORICAL / STALE INFORMATION: ...
PLANNED STATE (não implementado): ...
CONFLICTING EVIDENCE: <implementação vs intenção declarada, sem resolver>
UNKNOWNS: ...

CONTEXT STATUS: CURRENT | STALE | PARTIAL | INCONCLUSIVE
HANDOFF: REQUIRED | RECOMMENDED | NOT NEEDED <para qual próxima skill, se aplicável>
```

## Safeguards

1. memória antiga tratada como estado atual — proibido pelo Passo 2.
2. README/doc obsoleto tratado como verdade absoluta — proibido pelo Passo 2 (duas categorias, nunca uma vencendo silenciosamente).
3. inferência tratada como fato — proibido pelo Passo 5.
4. branch errada — mitigado pela declaração explícita de `REF/BRANCH` e checagem contra `TARGET REF` do input.
5. working tree ignorada — mitigado pelo Git snapshot (Passo 8) sempre discriminar dirty/staged/unstaged/untracked.
6. proposta futura tratada como implementação — proibido pelo Passo 4 (`PLANNED STATE`).
7. ausência de informação preenchida por suposição — proibido pelo Passo 4 (`UNKNOWN`).
8. contexto parcial representado como completo — `CONTEXT STATUS: PARTIAL` sempre declarado quando aplicável.
9. escopo de módulo representado como contexto do repo inteiro — `EVALUATION SCOPE` sempre explícito no output.
10. alteração do repositório durante a observação — proibido pela fronteira de execução (read-only sem exceção).
11. **HEAD substituindo working tree dirty silenciosamente** — proibido pelo Passo 3: as duas realidades (committed vs observado) sempre lado a lado quando divergem.
12. **execução de código do projeto para completar o contexto** — proibido pela fronteira de execução; incompletude declarada (`PARTIAL`) é sempre preferível a violar o boundary.

## Referências

- `references/acceptance-cases.md` — os 14 casos canônicos que validam esta skill, incluindo os 8 marcados como HARD ACCEPTANCE.
