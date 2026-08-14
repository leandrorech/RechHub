---
name: rech-deep-audit
description: "Realiza auditoria profunda e multi-camada, somente leitura, de código ou conteúdo/documento (clínico/técnico) de um projeto RECH, para encontrar e caracterizar defeitos — nunca corrige, nunca decide regressão ou release. Produz findings estruturados (FINDING ID, DOMAIN, SEVERITY, CONFIDENCE independentes, EVIDENCE via escala RAF E0-E5, STATUS CONFIRMED/PLAUSIBLE/FALSE_POSITIVE/INCONCLUSIVE) com escopo AUDITED/PARTIALLY_AUDITED/NOT_AUDITED explícito — nunca representa cobertura parcial como total nem ausência de achado como prova de correção. Use para 'auditar profundamente', revisão técnica sistemática, procurar bugs/inconsistências em múltiplas camadas, ou avaliar qualidade/segurança/arquitetura de forma abrangente. NÃO dispare para: corrigir bug já conhecido (rech-fix), verificar se mudança quebrou algo (rech-regression-guardian), decidir merge/release (rech-release-gate), estabelecer estado atual do repositório (rech-repo-context), ou revisão rápida sem pedido de auditoria profunda."
---

# RECH Deep Audit v2

## Missão e fronteiras

**"Há problemas neste código/conteúdo, e o sistema está correto, aqui e agora?"**

```
rech-repo-context         → "o que existe e qual é o estado atual?"
rech-deep-audit           → "há problemas e o sistema está correto, aqui e agora?"
rech-fix                  → "o problema aprovado foi corrigido corretamente?"
rech-regression-guardian  → "essa mudança quebrou algo previamente estabelecido?"
rech-release-gate         → "essa mudança está suficientemente validada para avançar?"
```

Esta skill **encontra e caracteriza** problemas. Ela não corrige, não decide regressão histórica sozinha, não autoriza release, e não substitui `rech-repo-context`.

### Regra absoluta: AUDIT = NO MODIFICATION

```
AUDIT = NO MODIFICATION
```

**Pode:** ler, analisar, executar verificações seguras, reproduzir problemas quando necessário para confirmar evidência, produzir evidência, classificar findings, sugerir direção de correção (nunca um patch pronto), identificar `CANDIDATE INVARIANT`.

**Não pode:** editar código, editar documentos, aplicar patch, usar `str_replace`/`create_file` no alvo da auditoria, commitar, alterar teste/requisito, ou transformar uma confirmação simples do usuário ("sim, aplica") em autorização de implementação. Essa era exatamente a falha da v1 — o campo "Fix sugerido" já entregava um patch pronto e um gate de confirmação leve autorizava escrita direta no repositório, contornando inteiramente o rigor que `rech-fix` formalizou (causa raiz, invariantes, escopo mínimo, teste RED→GREEN, regression guardian, release gate).

```
CODE:
rech-deep-audit → FINDING → decisão humana → rech-fix

CONTENT:
rech-deep-audit → CONTENT FINDING → decisão humana → CONTENT_CHANGE_HANDOFF
```

`CONTENT_CHANGE_HANDOFF` não é uma skill construída ainda — é só o nome do próximo passo conceitual para conteúdo/documento. Não criar `rech-content-fix` agora.

## Terminologia: reuso do RAF onde confirmado, extensão explícita onde não

Antes de inventar vocabulário, esta skill tenta reusar a terminologia epistemológica já canônica do RAF (RECH Audit Framework v0.99-RC). Isso só é válido para o que pôde ser **confirmado por texto real do documento** — não por memória ou inferência. Ver `references/finding-schema-and-raf-mapping.md` para o detalhamento completo, mas o resumo é:

- **Natureza da alegação** (`FATO`/`MEMÓRIA`/`PROPOSTA`): CONFIRMADO.
- **Força da evidência** (`E0`–`E5`): CONFIRMADO para `E1`–`E4`; `E0` e `E5` sem definição textual confirmada nesta verificação — use com o mesmo espírito da escala, mas confirme contra o documento antes de depender de precisão fina nos extremos.
- **Severidade**: CONFIRMADO para `BLOCKER`/`CRITICAL`/`HIGH`/`MEDIUM`/`LOW` (5 de 6 níveis); o 6º nível não pôde ser confirmado.
- **Confiança** (`Muito Alta`/`Alta`/`Moderada`/`Baixa`): nomes CONFIRMADOS. A **relação entre classe de evidência e nível de confiança NÃO é texto confirmado do RAF** — é uma correção proposta em auditoria adversarial anterior (RAF-03), sem confirmação de que foi mesclada ao texto canônico v0.99-RC. Tratada aqui como extensão explícita desta skill (`NOT DEFINED BY RAF`), não como regra RAF.
- **`STATUS`** (`CONFIRMED`/`PLAUSIBLE`/`FALSE_POSITIVE`/`INCONCLUSIVE`): o RAF não define este eixo — é uma **extensão explícita e genuína** desta skill, documentada como tal.

**Regra central sobre `STATUS`, que não é opcional:** `STATUS` nunca é uma função determinística da classe de evidência (`E0`–`E5`). A classe de evidência descreve *força/qualidade da evidência*; `STATUS` descreve *o resultado substantivo da avaliação do finding* — o que a evidência de fato mostrou, não quão forte ela é.

```
EVIDENCE STRENGTH ≠ FINDING STATUS
```

Evidência forte (E4/E5) pode sustentar tanto `CONFIRMED` (evidência demonstra que o defeito existe) quanto `FALSE_POSITIVE` (evidência demonstra que não existe) — a classe de evidência só determina se a skill *pode* afirmar algo definitivo em qualquer direção; o que ela afirma depende do conteúdo da evidência. Ver a tabela de decisão e os exemplos completos em `references/finding-schema-and-raf-mapping.md`.

## Domain model

```
DOMAIN: CODE | CONTENT | MIXED
```

Uma única skill, não duas, não um router. Compartilhado entre os domínios: contrato de entrada, modelo de evidência, modelo de finding, severidade, confiança, escopo/cobertura, tratamento de invariantes, output contract, handoff. Especializado por domínio: só as camadas de metodologia.

```
CODE    → camadas de auditoria de software (8 camadas, ver references/domain-profiles.md)
CONTENT → camadas de auditoria documental/factual/clínica (4 camadas, idem)
MIXED   → aplica ambos os perfis separadamente, nunca mistura evidência
           metodologicamente distinta no mesmo finding, e consolida ao final
```

Ver `references/domain-profiles.md` para as camadas completas de cada perfil.

## Passo 0 — Input contract

```
DEEP AUDIT INPUT

AUDIT TARGET: <obrigatório — arquivo, módulo, projeto, ou documento>
DOMAIN: CODE | CONTENT | MIXED <obrigatório>
TASK / QUESTION: <obrigatório — o que motivou a auditoria>
EVALUATION SCOPE: <obrigatório — delimita o que será de fato coberto>
REPO CONTEXT SNAPSHOT: <opcional — ver Passo 6>
KNOWN INVARIANTS: <opcional — fornecidos ou descobertos durante a auditoria>
USER-SUPPLIED REQUIREMENTS: <opcional>
BASELINE: <opcional — só quando genuinamente aplicável; ausência de
  baseline não impede a auditoria, só impede classificar algo como
  regressão, ver Passo 7>
```

`rech-deep-audit` audita o **estado atual**, sem exigir necessariamente um diff — isso a distingue estruturalmente de `rech-regression-guardian`, que sempre precisa de candidato vs baseline.

## Passo 1 — Evidence model

```
FACT               — verificado diretamente pela própria skill nesta auditoria
INFERENCE          — conclusão derivada de fatos, não afirmada por nenhuma fonte
UNKNOWN            — não determinável com as fontes disponíveis
CONFLICTING EVIDENCE — fontes discordam entre si (código × requisito ×
                        documentação), reportado sem a skill resolver
                        arbitrariamente qual lado está certo
```

Cada afirmação usada como evidência de um finding carrega também sua origem no vocabulário RAF (`FATO`/`MEMÓRIA`/`PROPOSTA`) e sua classe de evidência (`E0`–`E5`) — ver `references/finding-schema-and-raf-mapping.md` para a tabela completa e exemplos.

**Uma suspeita não vira finding confirmado sem evidência suficiente.** Para conteúdo clínico/factual, confirmar como `CONFIRMED` exige fonte identificável e adequada (guideline, protocolo, referência primária) — nunca confirmar uma afirmação clínica/factual apenas por memória do próprio modelo, mesmo que pareça familiar.

## Passo 2 — Finding model

```
FINDING ID
DOMAIN
TITLE

STATUS / CLASSIFICATION      (ver references/finding-schema-and-raf-mapping.md)
SEVERITY                     (escala RAF)
CONFIDENCE                   (escala RAF, independente de SEVERITY)

LOCATION
AFFECTED SCOPE

EVIDENCE
  FACTS
  INFERENCES

PROBLEM / IMPACT

RELATED INVARIANT
CANDIDATE INVARIANT

VERIFICATION / REPRODUCTION

RECOMMENDED NEXT STEP
```

Nunca usar o campo "Fix sugerido" (herança da v1, removido). Usar `RECOMMENDED NEXT STEP` — uma direção, não um patch pronto para aplicar. Template completo com exemplos em `references/finding-schema-and-raf-mapping.md`.

## Passo 3 — Severity × Confidence × Status são eixos independentes

```
SEVERITY: CRITICAL
CONFIDENCE: LOW
STATUS: PLAUSIBLE
```

Um problema potencialmente crítico pode ter confiança baixa (ainda não totalmente verificado); um problema certamente real pode ser de severidade baixa. O relatório nunca deve deixar essas três dimensões implícitas ou infladas uma pela outra.

`STATUS` em particular nunca é derivado mecanicamente da classe de evidência — ver "Terminologia" acima e `references/finding-schema-and-raf-mapping.md` para a regra completa (`EVIDENCE STRENGTH ≠ FINDING STATUS`) e os exemplos onde o mesmo nível de evidência (E5) sustenta `CONFIRMED` num caso e `FALSE_POSITIVE` noutro.

## Passo 4 — Invariant handling

Mesma disciplina já estabelecida nas quatro skills `LOCKED`:

```
Pode: vincular finding a invariante existente (RECH_INVARIANTS.md);
      detectar violação;
      registrar CANDIDATE INVARIANT.

Nunca: promover CANDIDATE INVARIANT a invariante oficial sozinha —
       essa decisão é sempre humana.
```

## Passo 5 — Scope / coverage model

```
AUDITED | PARTIALLY_AUDITED | NOT_AUDITED | OUT_OF_SCOPE
```

Declarado explicitamente no output para cada parte relevante do `AUDIT TARGET` — nunca implícito. Uma auditoria de três arquivos nunca é apresentada como "o projeto está correto".

**Clean audit** (nenhum finding): nunca apresentado como prova de correção total.

```
NO FINDINGS ≠ SYSTEM CORRECT
```

Formato obrigatório quando não há achados:
```
FINDINGS: NONE

AUDITED SCOPE: ...
METHODS USED: ...
NOT AUDITED: ...
LIMITATIONS: ...

CONCLUSION: No findings were identified within the audited scope and methods.
```

## Passo 6 — Relação com `rech-repo-context`

```
REPO CONTEXT: REQUIRED | RECOMMENDED | NOT NEEDED
```

`REQUIRED` quando ground truth atual é necessário (branch/estado incerto, projeto não tocado recentemente) e não há snapshot `CURRENT` já disponível. Nunca burocratizar auditorias triviais com contexto já suficiente — se a conversa já estabeleceu o estado relevante, ou o escopo é pequeno o bastante para verificar diretamente, repo-context não é obrigatório.

## Passo 7 — Relação com `rech-regression-guardian`

**Nunca** classificar um achado como `REGRESSION` sem baseline/change evidence adequado — isso é escopo exclusivo do guardian, com seu próprio contrato de evidência. Se há um defeito no estado atual, mas não há baseline disponível para comparar:

```
STATUS: current-state defect
```

nunca `REGRESSION`. Se durante a auditoria o usuário (ou o próprio contexto) sugerir que algo "quebrou" recentemente, isso é um sinal para recomendar `rech-regression-guardian` como próximo passo — não para a própria `deep-audit` fazer esse julgamento.

## Passo 8 — Relação com `rech-release-gate`

**Nunca** produzir `READY`, `BLOCKED`, ou `RELEASE_OK` como decisão de release. Findings desta skill podem alimentar uma decisão de release feita por outra etapa, mas a decisão em si nunca sai daqui.

## Passo 9 — Execution policy

Diferente de `rech-repo-context` (que nunca executa código do projeto), esta skill **pode** executar verificações quando necessário — mas com uma política explícita, não execução cega:

```
Default: SAFE / NON-DESTRUCTIVE EXECUTION

Permitido quando apropriado:
  - static analysis
  - linters
  - compiler/check
  - testes isolados conhecidos como seguros
  - diagnósticos read-only

Nunca executar cegamente:
  - chamadas de API reais (inclusive as chamadas client-side
    multi-provedor de IA já presentes em vários projetos RECH)
  - chamadas de rede com custo
  - migrations
  - escrita em banco de dados
  - acesso a produção
  - deploy
  - comandos dependentes de credenciais
  - scripts com efeito colateral desconhecido
  - fluxos de browser que mutam estado externo
```

Se houver risco de efeito colateral:

```
STOP → explica o risco → pede autorização, ou usa alternativa segura
```

A skill pode executar **para observar**. Nunca modifica o alvo para influenciar o resultado da própria auditoria — nem mesmo "só para confirmar", nem mesmo como parte do que seria uma verificação legítima.

## Output contract

Ver `references/finding-schema-and-raf-mapping.md` para o template completo por finding, e a seção Passo 5 acima para o formato de clean audit. O relatório final sempre responde:

```
What was audited?          → AUDITED / PARTIALLY_AUDITED / NOT_AUDITED
What was not audited?       → NOT_AUDITED / OUT_OF_SCOPE, explícito
What evidence was used?     → FACTS / INFERENCES por finding
What findings were confirmed? → STATUS: CONFIRMED
What remains uncertain?     → STATUS: PLAUSIBLE / INCONCLUSIVE
What is the severity?       → eixo independente
What is the confidence?     → eixo independente
What invariants involved?   → RELATED INVARIANT / CANDIDATE INVARIANT
What should happen next?    → RECOMMENDED NEXT STEP por finding, e um
                                resumo geral (ex.: "3 findings requerem
                                rech-fix", "1 requer rech-regression-guardian")
```

## Referências

- `references/finding-schema-and-raf-mapping.md` — template completo de finding, mapeamento de terminologia RAF, e a extensão mínima (`STATUS`) onde o RAF não cobre algo necessário.
- `references/domain-profiles.md` — as 8 camadas do perfil CODE, as 4 camadas do perfil CONTENT, e a regra de consolidação para MIXED.
- `references/execution-policy.md` — detalhamento da política de execução segura, com exemplos do ecossistema RECH.
- `references/acceptance-cases.md` — os 14 casos canônicos que validam esta skill, incluindo os marcados como HARD ACCEPTANCE.
