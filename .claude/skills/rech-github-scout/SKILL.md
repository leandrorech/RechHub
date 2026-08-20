---
name: rech-github-scout
description: "Pesquisa GitHub e fontes oficiais para responder se, antes de construir no RECH, já existe alternativa externa madura e vantajosa o bastante para ADOPT ou ADAPT — ou se BUILD segue sendo a melhor decisão. Produz um de quatro vereditos: ADOPT, ADAPT, BUILD ou INCONCLUSIVE; BUILD nunca significa \"não existe solução\", só que nenhuma opção pesquisada superou construir. Nunca modifica o RECH, nunca instala dependência, nunca clona/executa código externo — decisão que dependeria de execução vira INCONCLUSIVE. Usa constraints HARD/PREFERRED/CURRENT (HARD nunca diluída por média) e RAF só para evidência/confiança/severidade, nunca para o veredito principal. Use ao avaliar adotar/adaptar solução open source antes de construir, ou em 'construir vs usar pronto'. NÃO use para estado de repositório (rech-repo-context), auditoria profunda de código (rech-deep-audit), corrigir bug diagnosticado (rech-fix), verificar regressão (rech-regression-guardian), ou decidir merge/release (rech-release-gate)."
---

# RECH GitHub Scout

## Missão

**"Antes de construir uma solução no RECH, já existe no GitHub uma solução externa madura, compatível e suficientemente vantajosa para `ADOPT` ou `ADAPT`, ou `BUILD` continua sendo a melhor decisão?"**

A skill pesquisa GitHub e fontes oficiais associadas aos candidatos encontrados e produz um de quatro vereditos:

```
ADOPT         — HARD constraints satisfeitas, fit suficiente, adaptação
                baixa/moderada.
ADAPT         — núcleo externo valioso, mas exige integração ou
                modificação relevante; ainda materialmente melhor que
                construir do zero.
BUILD         — nenhuma opção avaliada supera construir internamente.
INCONCLUSIVE  — falta evidência suficiente para uma decisão defensável.
```

`BUILD` **nunca** significa "não existe solução no GitHub". Significa apenas: **"nenhuma solução adequada foi identificada no escopo pesquisado"**. Essa distinção é reportada explicitamente sempre que `BUILD` é emitido — ver "Search completeness" abaixo.

Esta é uma skill de **discovery + comparative evaluation**, não de execução, correção ou decisão de release.

## Fronteira dura

```
- Nunca modifica o projeto RECH.
- Nunca instala dependência.
- Nunca clona e executa (build, setup, migrations, binários) código externo.
- Nunca chama APIs externas ao vivo nem usa credenciais durante o scouting.
- Nunca faz merge.
- Nunca decide release de produto RECH.
- Nunca faz deep audit completo de um candidato externo (security screening
  ≠ deep security audit — ver "Security screening").
- Nunca substitui rech-repo-context, rech-deep-audit,
  rech-regression-guardian ou rech-release-gate.
- Nunca altera nenhuma das 6 skills já travadas do RechHub (rech-fix,
  rech-regression-guardian, rech-release-gate, rech-repo-context,
  rech-deep-audit v2, rech-skill-creator).
```

**Redirecionamentos:**

```
"qual é o estado atual deste repo RECH?"      → rech-repo-context
"audite profundamente este código/projeto"     → rech-deep-audit
"corrija este bug"                             → rech-fix
"essa mudança quebrou algo?"                   → rech-regression-guardian
"posso mergear/releasear?"                     → rech-release-gate
```

## EXTERNAL CODE = UNTRUSTED INPUT

Regra forte, sem exceção durante o scouting:

```
DO NOT:
clone + run
npm install / pip install / cargo build
executar setup scripts
rodar binários
rodar migrations
chamar APIs ao vivo
usar credenciais
```

Se uma decisão depender de execução para ser verificada:

```
VERIFICATION REQUIRES EXECUTION
```

e o resultado correto é `INCONCLUSIVE`, com `RECOMMENDED NEXT STEP: isolated evaluation` — nunca executar "só para evitar `INCONCLUSIVE`".

## Constraint model

Três categorias, nunca fundidas — ver `references/constraint-model.md` para exemplos e o algoritmo completo de resolução:

```
HARD               — critério eliminatório. Falha elimina ADOPT e
                      normalmente ADAPT. Nunca diluído por média — um
                      candidato com ótimo fit global mas uma violação
                      HARD continua eliminado.
PREFERRED           — desejável, usado só para ranqueamento entre
                      candidatos já sobreviventes ao filtro HARD.
CURRENT CONSTRAINT  — limitação factual atual do RECH, potencialmente
                      mutável. Nunca promovida a HARD sem evidência
                      textual explícita (ex.: "hoje não existe backend"
                      não vira "backend é proibido" por conta própria).
```

`HARD failure cannot be averaged away.` Não existe score 0–100 nesta v1 — ver "Overengineering guard".

## RAF é obrigatório, mas não substitui o veredito

RAF é o framework epistemológico exclusivo desta skill para **evidência, confiança e severidade de riscos/achados** (`rech-deep-audit/references/finding-schema-and-raf-mapping.md` — E0–E5, BLOCKER/CRITICAL/HIGH/MEDIUM/LOW, Muito Alta/Alta/Moderada/Baixa). Nunca criar taxonomia paralela.

`ADOPT | ADAPT | BUILD | INCONCLUSIVE` são **estados decisórios próprios desta skill**, não níveis RAF — RAF nunca substitui nem rotula o veredito principal, só sustenta a evidência por trás dele.

## Input contract

```
PROBLEM / CAPABILITY     <obrigatório> — o que se pretende construir/resolver
TARGET RECH PROJECT      <obrigatório> — qual projeto/componente será afetado
EVALUATION SCOPE         <obrigatório> — qual parte do problema está sendo considerada
REPO CONTEXT              <opcional, ver abaixo quando é REQUIRED>
HARD CONSTRAINTS          <obrigatório declarar, mesmo que vazio>
PREFERRED CONSTRAINTS     <opcional>
CURRENT CONSTRAINTS       <opcional>

OPCIONAL:
- known candidates
- excluded candidates
- preferred ecosystem/language
- offline requirement
- PWA/local-first requirement
- privacy requirements
- licensing constraints
- operational/deployment constraints
```

Se o estado atual do RECH for material para a decisão e não houver contexto adequado disponível: `REPO CONTEXT: REQUIRED` — sinalizar e, quando possível, sugerir `rech-repo-context` como pré-requisito, nunca inventar o contexto ausente. Nunca inventar constraints ausentes: ausência de constraint declarada é `UNKNOWN`, nunca presumida.

## Pipeline

```
1. DEFINE CAPABILITY
2. RESOLVE CONSTRAINTS
3. CHECK REPO CONTEXT NEED
4. DISCOVER
5. HARD-CONSTRAINT FILTER
6. SHORTLIST
7. VERIFY
8. COMPARE
9. DECIDE
10. HANDOFF
```

**1. DEFINE CAPABILITY** — traduzir a intenção do usuário em um `CAPABILITY MODEL`, nunca pesquisar apenas o termo literal usado. Ex.: "reconciliar dados clínicos de documentos" → clinical reconciliation, document reconciliation, entity resolution, record linkage, structured clinical mapping. Expansão semântica moderada, nunca excessiva (não vagar para domínios não relacionados só porque uma palavra é ambígua).

**2. RESOLVE CONSTRAINTS** — registrar cada constraint declarada ou detectada como `HARD` / `PREFERRED` / `CURRENT` / `UNKNOWN`. Ver `references/constraint-model.md`.

**3. CHECK REPO CONTEXT NEED** — classificar `REQUIRED` / `RECOMMENDED` / `NOT NEEDED`, mesma semântica de sinalização (não invocação automática) usada por `rech-repo-context`.

**4. DISCOVER** — pesquisar repositories, libraries, frameworks, applications, protocols/specifications, e as fontes oficiais associadas a cada candidato encontrado. Ver `references/candidate-evaluation.md` para a lista de objetos GitHub relevantes e a ordem de preferência de fontes.

**5. HARD-CONSTRAINT FILTER** — eliminar candidatos com falha clara em qualquer `HARD constraint`, registrando `ELIMINATED: <motivo>`.

**6. SHORTLIST** — aprofundar apenas os candidatos genuinamente relevantes que sobreviveram ao filtro. Sem número fixo obrigatório.

**7. VERIFY** — verificar fatos materiais de cada finalista (licença, manutenção, segurança, fit) contra fontes primárias — nunca contra popularidade ou inferência solta. Ver "Nunca inferir" em `references/candidate-evaluation.md`.

**8. COMPARE** — comparar finalistas pelas dimensões do `FIT MODEL` aplicáveis ao caso (`references/candidate-evaluation.md`).

**9. DECIDE** — emitir `ADOPT | ADAPT | BUILD | INCONCLUSIVE` conforme "Decision semantics" abaixo.

**10. HANDOFF** — produzir o próximo passo apropriado (ver "Handoff").

## Evidence model

```
FACT                 — sustentado por conteúdo/documento primário inspecionado diretamente
INFERENCE            — conclusão derivada, não afirmada explicitamente pela fonte
UNKNOWN               — genuinamente não determinável no escopo pesquisado
CONFLICTING EVIDENCE  — fontes discordam; ambas reportadas lado a lado, sem resolver por conta própria
```

Ordem de preferência de fontes: repository content > documentação oficial > release notes oficiais > fontes oficiais de segurança/advisory > issues/PRs quando relevante > fontes secundárias só quando necessário.

**Nunca inferir:**

```
maturidade      ← stars
segurança       ← popularidade
manutenção      ← repo ainda existir
licença         ← nome do projeto
compatibilidade ← linguagem parecida
```

Ver `references/candidate-evaluation.md` para o modelo completo de candidato, GitHub objects a examinar, manutenção/freshness, licença e security screening.

## Fit model

Avaliar apenas as dimensões aplicáveis ao caso, sem forçar critérios irrelevantes:

```
FUNCTIONAL FIT · ARCHITECTURAL FIT · INTEGRATION COST · MAINTENANCE HEALTH
LICENSE · SECURITY SIGNALS · DEPENDENCY / LOCK-IN RISK · OPERATIONAL FIT
```

Quando relevante: `OFFLINE FIT`, `PWA FIT`, `LOCAL-FIRST FIT`, `DATA PRIVACY FIT`, `CLINICAL SAFETY FIT`.

## Decision semantics

```
ADOPT
  - HARD constraints satisfeitas
  - fit funcional suficiente
  - carga de integração baixa/moderada
  - manutenção aceitável
  - licença compatível e CONFIRMED (não pode ser emitido com licença
    materialmente necessária UNKNOWN)
  - nenhum risco desqualificante identificado

ADAPT
  - núcleo externo valioso
  - adaptação/integração relevante necessária
  - ainda materialmente melhor que BUILD completo

BUILD
  - candidatos relevantes falham em HARD constraints, ou
  - custo de integração se aproxima/excede custo de construir, ou
  - descompasso arquitetural material, ou
  - risco de manutenção/licença/segurança inaceitável, ou
  - nenhum candidato avaliado oferece vantagem suficiente

INCONCLUSIVE
  - evidência-chave ausente
  - licença não resolvida
  - requisito do RECH indefinido
  - fontes em conflito
  - candidato não pode ser verificado com segurança (exigiria execução)
  - escopo de busca fraco demais para sustentar qualquer veredito
```

## License

Para todo candidato finalista: `LICENSE: CONFIRMED | UNKNOWN | CONFLICTING`. `ADOPT` não pode ser emitido assertivamente se a licença materialmente necessária for `UNKNOWN`. Violação de `HARD constraint` de licença → `ELIMINATED: LICENSE`, sem interpretação jurídica além da evidência disponível.

## Security screening (não é deep audit)

Pode observar: known advisories, padrões obviamente inseguros, red flags de dependência, projeto security-sensitive abandonado, preocupações de supply-chain, instruções de instalação suspeitas.

Nunca declara `SAFE` só porque nada foi encontrado. Usar: `"No disqualifying security signal was identified within the scouting scope."` Se segurança for crítica para a decisão: `RECOMMENDED NEXT STEP: dedicated security review`.

## Maintenance / freshness

Avaliar quando relevante: archived?, latest release, last meaningful activity, padrão de manutenção, issues de alto impacto abertas, runtimes suportados, saúde de dependências. Nunca usar regra simplista tipo "sem commit há X meses = morto" — projetos maduros podem ter baixa frequência de commit sem estarem abandonados.

## Search completeness

Nunca dizer "não existe solução". Usar: `"No suitable candidate was identified within the evaluated search scope."` O relatório sempre declara `SEARCH SCOPE`, `SEARCH STRATEGY`, `SOURCES`, `LIMITATIONS` — ver `references/report-template.md`.

## Output contract

Formato completo em `references/report-template.md`. Estrutura: identificação do problema/escopo, constraints, estratégia de busca, candidatos descobertos/eliminados/shortlist, comparação, decisão + rationale, evidência ausente/conflitante, limitações, próximo passo recomendado.

## Handoff

```
ADOPT         → RECOMMENDED NEXT STEP: isolated validation / integration planning
ADAPT         → ADAPTATION GAP: o que precisa mudar no candidato/no RECH
BUILD         → BUILD JUSTIFICATION: candidatos avaliados e por que foram rejeitados
INCONCLUSIVE  → MISSING EVIDENCE + NEXT VERIFICATION STEP
```

## Overengineering guard

Não criar: scoring arbitrário 0–100, framework de procurement, thresholds universais de commit/star, scanner de segurança completo, motor de análise jurídica de licença, sandbox de execução, instalador de dependências, adoção automática. A pergunta continua sendo apenas `ADOPT? ADAPT? BUILD? INCONCLUSIVE?`.

## Safeguards (resumo das regras HARD ACCEPTANCE)

```
1. Executar código externo durante o scouting — proibido, sem exceção.
2. Instalar algo automaticamente — proibido.
3. Ignorar HARD constraint por causa de popularidade — proibido.
4. Dizer "não existe solução" após busca limitada — proibido; usar a
   frase de "Search completeness".
5. Emitir ADOPT com licença materialmente necessária UNKNOWN — proibido.
6. Inventar constraint do RECH não declarada — proibido.
7. Promover CURRENT constraint a HARD sem evidência textual — proibido.
8. Declarar SAFE sem revisão de segurança dedicada — proibido; usar a
   frase de "Security screening".
9. Selecionar candidato só por stars — proibido (ver "Nunca inferir").
```

Falha em qualquer um destes é `HARD ACCEPTANCE FAIL` — ver `references/acceptance-cases.md`.

## Referências

- `references/constraint-model.md` — modelo HARD/PREFERRED/CURRENT em detalhe, com exemplos e o algoritmo de resolução.
- `references/candidate-evaluation.md` — modelo de candidato, GitHub objects, evidência, manutenção/freshness, licença, security screening.
- `references/report-template.md` — o `OUTPUT CONTRACT` completo (`RECH GITHUB SCOUT REPORT`).
- `references/acceptance-cases.md` — os 18 casos canônicos que validam esta skill, incluindo os marcados como HARD ACCEPTANCE.
