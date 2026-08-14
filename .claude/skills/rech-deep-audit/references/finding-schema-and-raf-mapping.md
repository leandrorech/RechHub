# Finding schema e mapeamento de terminologia RAF

## Por que reusar o RAF, e o que pôde ser verificado de fato

O ecossistema RECH já tem uma epistemologia formal — o RAF (RECH Audit Framework), atualmente na v0.99-RC. Criar uma segunda taxonomia paralela fragmentaria a linguagem de governança do ecossistema inteiro (esse erro já foi identificado e corrigido em outra frente de trabalho: uma taxonomia de 7 rótulos proposta para `rech-skill-creator` foi rejeitada como sistema paralelo e mapeada de volta ao RAF). Esta skill segue o mesmo princípio: **mapear, não duplicar**.

**Limite real desta verificação**: o `.docx` do RAF v0.99-RC não estava disponível na sessão em que este documento foi escrito. O que segue é dividido explicitamente entre o que foi confirmado por citação direta de texto lido em sessões anteriores, e o que não pôde ser confirmado — tratado como `NOT DEFINED BY RAF` (extensão desta skill) até verificação real contra o documento.

## Natureza da alegação: FATO / MEMÓRIA / PROPOSTA — CONFIRMADO

```
FATO      — verificado diretamente pela própria skill nesta auditoria
MEMÓRIA   — relato/memória conversacional, ou afirmação de outra IA/sessão,
            não verificada de forma independente nesta auditoria
PROPOSTA  — decisão de design ou plano documentado, ainda não implementado
```

Equivalência com o modelo `FACT`/`INFERENCE`/`UNKNOWN` desta skill: `FATO` alimenta `FACT`; `MEMÓRIA` sozinha nunca vira `FACT`; `PROPOSTA` nunca é tratada como estado atual.

## Força da evidência: escala E0–E5 — PARCIALMENTE CONFIRMADO

```
E0  — NOT DEFINED BY RAF nesta verificação (presumivelmente "nenhuma
      evidência/especulação pura", por ser o extremo inferior da escala,
      mas sem citação direta do texto confirmando a definição exata)
E1  — CONFIRMADO: inferência estrutural (conclusão derivada, sem observação direta)
E2  — CONFIRMADO: observação estática (visto diretamente, não executado/testado)
E3  — CONFIRMADO: demonstração lógica (mecanismo demonstrável, mesmo sem reprodução)
E4  — CONFIRMADO: reproduzido (código: versão/hash/commit + passos executados;
      documento: confirmado por comparação direta e determinística dentro
      do próprio artefato ou da fonte primária citada)
E5  — NOT DEFINED BY RAF nesta verificação (presumivelmente o nível mais
      forte disponível, mas sem citação direta confirmando a definição)
```

Todo finding cita o nível E que sustenta sua evidência. Onde `E0`/`E5` forem citados, isso é feito com a ressalva de que a definição operacional exata ainda não foi confirmada contra o documento — use com o mesmo espírito da escala (mais forte = E5, mais fraco = E0), mas confirme a definição textual antes de qualquer uso que dependa de precisão fina no limite superior/inferior.

## Severidade — PARCIALMENTE CONFIRMADO

```
BLOCKER, CRITICAL, HIGH, MEDIUM, LOW  — CONFIRMADOS (uso consistente
  em achados RAF reais e na auditoria adversarial do próprio RAF)
6º nível — NOT DEFINED BY RAF nesta verificação. Há um indício textual
  ("de BLOCKER a INFO/IMPROVEMENT") mas não ficou claro se é um nome
  único ou dois conceitos distintos. Não presuma qual dos dois — se
  precisar de um 6º nível antes de confirmar contra o documento, use
  `LOW` como piso e sinalize explicitamente que a nomenclatura abaixo
  de `LOW` não está confirmada.
```

## Confiança — nomes CONFIRMADOS, ancoragem por evidência NOT DEFINED BY RAF

```
Muito Alta | Alta | Moderada | Baixa   — CONFIRMADOS (os 4 nomes)
```

**A relação "classe de evidência → nível de confiança" NÃO é texto confirmado do RAF v0.99-RC.** O que existe é uma correção *proposta* em uma auditoria adversarial anterior do RAF (sobre a versão v0.95), sinalizada como necessária ("Necessidade de alteração antes da v1.0: Sim") — sem confirmação de que foi de fato mesclada ao texto canônico. Por isso, esta skill trata a tabela abaixo como **extensão explícita da `rech-deep-audit`**, não como regra RAF:

```
NOT DEFINED BY RAF — EXTENSÃO DA rech-deep-audit

Ancoragem sugerida (ponto de partida, ajustável com justificativa):
  E4/E5              → tende a Muito Alta
  E2/E3 sem conflito  → tende a Alta
  E1                 → tende a Moderada
  E0                 → Baixa
```

Esta ancoragem informa `CONFIDENCE`, mas — ver seção seguinte — **nunca determina `STATUS` sozinha**.

## STATUS — extensão explícita da rech-deep-audit, desacoplada de EVIDENCE

O RAF não define um eixo para "este finding foi verificado como problema real, ainda é suspeita, ou foi investigado e descartado" — isso é uma extensão genuína desta skill, não RAF.

```
STATUS: CONFIRMED | PLAUSIBLE | FALSE_POSITIVE | INCONCLUSIVE
```

**Regra corrigida — a mais importante desta seção:**

```
EVIDENCE CLASS (E0–E5)  →  força/qualidade da evidência
STATUS                  →  resultado substantivo da avaliação do finding
CONFIDENCE               →  grau de confiança nessa classificação
```

`STATUS` **não é** uma função determinística de `E0–E5`. A classe de evidência **limita quais valores de `STATUS` são epistemicamente defensáveis**, mas não escolhe qual deles se aplica — isso depende do que a evidência de fato mostra, não de quão forte ela é:

```
EVIDENCE STRENGTH ≠ FINDING STATUS
```

**Exemplo obrigatório** (mesmo nível de evidência, conclusões opostas):

```
E5 evidence supporting the defect  → STATUS: CONFIRMED
E5 evidence refuting the defect    → STATUS: FALSE_POSITIVE
```

As duas são igualmente legítimas em E5 — a evidência forte só garante que a skill pode afirmar *algo* com confiança alta; o que ela afirma depende do conteúdo da evidência, não do seu nível.

### Como decidir STATUS na prática

1. Avalie **o que a evidência mostra**: o defeito existe, não existe, parece existir mas não foi totalmente verificado, ou não dá para saber?
2. Verifique se a classe de evidência disponível **sustenta** a afirmação pretendida:

```
Para declarar CONFIRMED ou FALSE_POSITIVE (afirmações definitivas em
  qualquer direção): exige E4/E5. Declarar qualquer um dos dois com
  evidência E0-E3 não é permitido — use PLAUSIBLE ou INCONCLUSIVE.

PLAUSIBLE: evidência (tipicamente E1-E3) sugere que o defeito pode
  existir, mas não é forte o suficiente para confirmar nem para
  descartar com segurança.

INCONCLUSIVE: evidência insuficiente, conflitante, ou não confiável o
  bastante para determinar o estado do finding em qualquer direção —
  independentemente do nível E nominal alegado.
```

3. `FALSE_POSITIVE` é sempre um resultado de investigação ativa que refutou a suspeita com evidência forte (E4/E5) — nunca use `FALSE_POSITIVE` só porque a evidência é fraca (isso é `INCONCLUSIVE` ou simplesmente não reportar).

## Template completo por finding

```
FINDING ID: <ex. DA-RD-001>
DOMAIN: CODE | CONTENT

TITLE: <resumo de uma linha>

STATUS: CONFIRMED | PLAUSIBLE | FALSE_POSITIVE | INCONCLUSIVE
SEVERITY: <escala RAF>
CONFIDENCE: <escala RAF>

LOCATION: <arquivo:linha ou seção>
AFFECTED SCOPE: <o que exatamente é afetado>

EVIDENCE:
  FACTS: <lista, cada uma com natureza FATO e nível E>
  INFERENCES: <lista, cada uma rotulada como tal, com o(s) fato(s) de origem citado(s)>

PROBLEM / IMPACT: <explicação técnica/clínica do erro e sua consequência>

RELATED INVARIANT: <ID, se houver vínculo>
CANDIDATE INVARIANT: <descrição, se detectado e não promovido>

VERIFICATION / REPRODUCTION: <como foi verificado — nível E citado — e o
  que a verificação de fato mostrou (a favor ou contra o defeito)>

RECOMMENDED NEXT STEP: <direção, nunca patch pronto>
```

## Exemplo A — CRITICAL severity, LOW confidence, STATUS: PLAUSIBLE

```
FINDING ID: DA-RD-014
DOMAIN: CODE
TITLE: Possível vazamento de estado entre sessões concorrentes no cache de preview

STATUS: PLAUSIBLE
SEVERITY: CRITICAL
CONFIDENCE: Moderada

LOCATION: src/preview/cacheManager.ts:88-104
AFFECTED SCOPE: Preview de documentos em uso concorrente por múltiplas abas

EVIDENCE:
  FACTS:
    - [FATO, E2] cacheManager usa uma variável de módulo (não por sessão)
      para armazenar o último preview gerado
  INFERENCES:
    - [E1] Em teoria, duas abas processando documentos diferentes ao mesmo
      tempo poderiam sobrescrever o cache uma da outra — não foi
      reproduzido nesta auditoria

PROBLEM / IMPACT: Se confirmado, um usuário poderia ver o preview do
  documento de outra aba/sessão — risco de confusão clínica.

RELATED INVARIANT: nenhum vinculado — CANDIDATE INVARIANT abaixo
CANDIDATE INVARIANT: "Preview nunca deve misturar estado entre sessões
  concorrentes." Evidência: este finding. Recommendation: considerar
  formalizar após confirmação.

VERIFICATION / REPRODUCTION: não reproduzido (E1/E2) — precisaria de
  teste com duas sessões simultâneas reais para elevar a E4/E5 e
  permitir declarar CONFIRMED ou FALSE_POSITIVE.

RECOMMENDED NEXT STEP: reprodução controlada antes de encaminhar para
  rech-fix — a evidência atual (E1/E2) não sustenta CONFIRMED nem
  FALSE_POSITIVE, então o finding permanece PLAUSIBLE até que a
  reprodução aconteça.
```

## Exemplo B — mesmo nível de evidência (E5), conclusões opostas

```
Cenário 1 — defeito confirmado:
  Reprodução completa (E5): duas abas em ambiente de teste real
  sobrescrevem o cache uma da outra, comportamento observado e
  documentado passo a passo.
  → STATUS: CONFIRMED, CONFIDENCE: Muito Alta

Cenário 2 — mesma suspeita, mesmo rigor de investigação (E5), resultado oposto:
  Reprodução completa (E5): o mesmo teste roda com duas abas reais e o
  cache se comporta corretamente — cada sessão mantém seu próprio
  estado (o código na verdade usa um Map por sessão, não uma variável
  de módulo simples como pareceu na leitura inicial).
  → STATUS: FALSE_POSITIVE, CONFIDENCE: Muito Alta
```

Nos dois cenários a evidência é igualmente forte (E5) — a diferença está no que a reprodução de fato mostrou, não em quão bem ela foi conduzida. Isso é o que a regra `EVIDENCE STRENGTH ≠ FINDING STATUS` protege.
