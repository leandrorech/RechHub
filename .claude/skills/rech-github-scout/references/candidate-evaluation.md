# Candidate evaluation — rech-github-scout

## GitHub objects a examinar

Quando relevante para a decisão — não é obrigatório consultar tudo sempre;
escolher apenas o necessário:

```
repository metadata      README                   LICENSE
package manifests        directory structure       releases
tags                     branches                   issues
pull requests            Actions / CI status        security advisories
dependency manifests     supported runtime/version metadata
archived status          last meaningful activity
```

## Evidence model

```
FACT                  — sustentado por conteúdo/documento primário
                         inspecionado diretamente pela skill.
INFERENCE             — conclusão derivada de fato(s), não afirmada
                         explicitamente por nenhuma fonte; sempre rotulada
                         como tal e citando o fato-base.
UNKNOWN                — genuinamente não determinável no escopo pesquisado.
CONFLICTING EVIDENCE   — fontes discordam; reportadas lado a lado, sem
                         resolver qual está "certa".
```

Ordem de preferência de fontes (mais confiável primeiro):

```
1. repository content
2. documentação oficial
3. release notes oficiais
4. fontes oficiais de segurança/advisory
5. issues / pull requests, quando relevante
6. fontes secundárias, só quando necessário
```

**Nunca inferir** (violações destas equivalências são `HARD ACCEPTANCE
FAIL` — ver `acceptance-cases.md`):

```
maturidade       ⇍  stars
segurança         ⇍  popularidade
manutenção        ⇍  repo ainda existir
licença           ⇍  nome do projeto
compatibilidade   ⇍  linguagem parecida
```

## Candidate model

Estrutura enxuta, sem campos sem utilidade real:

```
CANDIDATE ID
NAME
REPOSITORY / OFFICIAL SOURCE
TYPE                       (repository | library | framework | application
                             | protocol/specification)

RELEVANT CAPABILITY

HARD CONSTRAINTS:          PASS | FAIL | UNKNOWN

FUNCTIONAL FIT:
ARCHITECTURAL FIT:
INTEGRATION COST:

MAINTENANCE:
LICENSE:                    CONFIRMED | UNKNOWN | CONFLICTING
SECURITY SIGNALS:
DEPENDENCY / LOCK-IN:

KEY EVIDENCE:
GAPS:

DISPOSITION:                SHORTLISTED | ELIMINATED (+ motivo se ELIMINATED)
```

## Maintenance / freshness

Avaliar quando relevante:

```
ARCHIVED?
LATEST RELEASE
LAST MEANINGFUL ACTIVITY
MAINTENANCE PATTERN
OPEN HIGH-IMPACT ISSUES
SUPPORTED RUNTIMES
DEPENDENCY HEALTH
```

**Nunca** usar regra simplista do tipo "sem commit há X meses = morto".
Projetos maduros e estáveis podem ter baixa frequência de commit sem
estarem abandonados — a evidência relevante é o padrão (releases
regulares, issues respondidas, security advisories atendidos), não a
frequência bruta de commits.

## License

Para todo candidato finalista: `LICENSE: CONFIRMED | UNKNOWN | CONFLICTING`.

- `ADOPT` não pode ser emitido assertivamente se a licença materialmente
  necessária for `UNKNOWN`.
- Se a licença viola uma `HARD constraint`: `ELIMINATED: LICENSE`.
- Sem interpretação jurídica além da evidência textual disponível — a
  skill relata o que o arquivo `LICENSE`/manifesto declara, não emite
  parecer legal.

## Security screening (não é deep security audit)

Esta skill faz **screening**, não auditoria de segurança profunda —
`rech-deep-audit` é a skill correta para isso, e ainda assim seria sobre
código RECH, não sobre um candidato externo.

Pode observar, quando aplicável:

```
known advisories
padrões obviamente inseguros
red flags de dependência
projeto security-sensitive abandonado
supply-chain concerns
instruções de instalação suspeitas (ex.: "curl | bash" sem verificação)
```

**Nunca** declarar `SAFE` só porque nada foi encontrado — ausência de
achado não é prova de segurança. Frase padrão:

```
No disqualifying security signal was identified within the scouting scope.
```

Se segurança for crítica para a decisão: `RECOMMENDED NEXT STEP: dedicated
security review`.

## No execution of external code

Regra forte, sem exceção durante o scouting:

```
DO NOT:
clone + run              npm install / pip install / cargo build
executar setup scripts   rodar binários
rodar migrations         chamar APIs ao vivo
usar credenciais
```

Se uma decisão depender de verificação por execução:

```
VERIFICATION REQUIRES EXECUTION
```

→ `INCONCLUSIVE`, com `RECOMMENDED NEXT STEP: isolated evaluation`. Nunca
executar código só para evitar produzir `INCONCLUSIVE` — essa é uma
condição de `HARD ACCEPTANCE FAIL`.

## Fit model

Avaliar apenas as dimensões aplicáveis ao caso concreto, sem forçar
critérios irrelevantes:

```
FUNCTIONAL FIT        ARCHITECTURAL FIT      INTEGRATION COST
MAINTENANCE HEALTH     LICENSE                 SECURITY SIGNALS
DEPENDENCY / LOCK-IN RISK                       OPERATIONAL FIT
```

Quando relevante ao domínio RECH:

```
OFFLINE FIT     PWA FIT     LOCAL-FIRST FIT
DATA PRIVACY FIT     CLINICAL SAFETY FIT
```
