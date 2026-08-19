# RechHub

Centro de governança, qualidade, contratos e coordenação do Ecossistema RECH.

> O RechHub não é um prontuário nem um aplicativo clínico. Ele organiza como os projetos RECH são definidos, auditados, corrigidos, validados, versionados e integrados.

## Missão

Manter uma visão factual e auditável do ecossistema, impedir sobreposição silenciosa entre projetos e fornecer uma esteira reprodutível para trabalho humano e assistido por IA.

O RechHub deve responder:

- quais projetos existem;
- qual função pertence a cada projeto;
- qual é o estado verificável de cada repositório;
- quais invariantes e contratos precisam ser preservados;
- quais mudanças estão em andamento;
- quais testes, auditorias e gates sustentam um merge ou release;
- quais bloqueadores e próximos passos permanecem abertos.

## Estado atual

Snapshot documental: **2026-08-19**

### Em `main`

Cinco skills da esteira RECH:

| Skill | Pergunta principal |
|---|---|
| `rech-repo-context` | Qual é o estado real e atual do repositório? |
| `rech-deep-audit` | Há problemas no sistema ou conteúdo atual? |
| `rech-fix` | O problema específico e aprovado foi corrigido corretamente? |
| `rech-regression-guardian` | A mudança quebrou algo previamente garantido? |
| `rech-release-gate` | A evidência disponível permite avançar para merge/release? |

Essas cinco skills são tratadas como **travadas** no rollout atual. Não devem ser reabertas apenas para aperfeiçoamento abstrato; exigem nova evidência de uso real.

### Em desenvolvimento

A branch `feat/rech-skill-creator-v1` contém a candidata do `rech-skill-creator`, com contratos, casos de aceite, gates, scripts e testes.

A existência da branch não equivale a release. A promoção para `main` depende dos critérios de aceite, regressão e release definidos para o rollout.

### Ainda não materializado

O RechHub ainda não possui, em `main`:

- registro canônico de todos os projetos;
- `PROJECT_STATE.md` global;
- arquitetura e mapa de dependências;
- matriz de versões e releases;
- ADRs das decisões estruturais;
- schemas compartilhados;
- automação de saúde cross-repo;
- dashboard do ecossistema.

Esses itens pertencem ao roadmap, não ao estado atual.

## Esteira de qualidade

```text
REPO CONTEXT
     ↓
DEEP AUDIT
     ↓
DECISÃO HUMANA
     ↓
FIX
     ↓
REGRESSION GUARDIAN
     ↓
RELEASE GATE
     ↓
MERGE / RELEASE
```

### Regras invariantes

1. Etapas não são puladas silenciosamente.
2. Auditoria não autoriza correção.
3. Finding não é decisão de produto.
4. Fix corrige apenas o problema aprovado.
5. Requisito/teste não é afrouxado para produzir resultado verde.
6. Ausência de evidência obrigatória não é evidência de segurança.
7. Regressão não resolvida não vira READY por urgência.
8. Skill travada só é reaberta com nova evidência real.
9. Estado do GitHub prevalece sobre memória de chat ou handoff desatualizado.
10. Conteúdo gerado por IA exige promoção humana explícita.

## Ecossistema e propriedade de domínio

| Projeto | Função proprietária |
|---|---|
| [RechStudy](https://github.com/leandrorech/RechStudy) | Estudo, revisão, questões, simulados, calculadoras e produção assistida |
| [RechDocs](https://github.com/leandrorech/RechDocs) | Documentação clínica e transformação rastreável de fontes |
| [RechShift](https://github.com/leandrorech/RechShift) | Passagem operacional de plantão e acompanhamento em UTI |
| [RechSupps](https://github.com/leandrorech/RechSupps) | Suplementos e migração arquitetural para o futuro domínio RechDrugs |
| [RechTrauma](https://github.com/leandrorech/RechTrauma) | Atendimento inicial e reavaliação estruturada do trauma |
| [RechER](https://github.com/leandrorech/RechER) | Emergências clínicas não traumáticas |
| [RechTEMI](https://github.com/leandrorech/RechTEMI) | Estrutura editorial e governança do Livro RECH–TEMI |
| [RAF](https://github.com/leandrorech/RAF) | Framework normativo de auditoria e qualidade |
| RechExams | Domínio planejado de exames e interpretação |
| RechDrugs | Evolução planejada do RechSupps para farmacologia integral |

### Regra de proprietário único

Cada capacidade deve possuir uma fonte canônica. Outros projetos podem consumir, apresentar ou ensinar o conteúdo, mas não criar silenciosamente uma segunda autoridade concorrente.

## Fronteiras do RechHub

### Pertence ao RechHub

- skills e seus contratos;
- governança do portfólio;
- inventário de projetos;
- arquitetura e ADRs;
- schemas compartilhados;
- versionamento e compatibilidade;
- matriz de release;
- relatórios cross-repo;
- automação de verificação;
- políticas de integração e IA.

### Não pertence ao RechHub

- prontuários ou dados identificáveis de pacientes;
- manuscrito integral do Livro RECH–TEMI;
- cópias dos aplicativos de cada repositório;
- banco clínico duplicado de medicamentos ou exames;
- chaves de API;
- lógica clínica proprietária dos módulos;
- outputs de IA promovidos sem decisão humana;
- merges automáticos que contornem os gates.

## Relação com o RAF

O RAF é a fonte normativa da metodologia de auditoria. O RechHub abriga implementações operacionais — skills, gates, scripts e contratos — derivadas dessa metodologia.

Uma implementação no RechHub não altera silenciosamente a norma do RAF. Divergências devem ser registradas e resolvidas explicitamente.

## Roadmap

### G0 — Fechar o rollout do `rech-skill-creator`

1. executar os casos de aceite;
2. fechar/registrar defeitos;
3. executar gates de schema, validade, isolamento e integridade;
4. executar regression guardian;
5. executar release gate;
6. promover somente com veredito compatível.

### G1 — Constituição de governança

Planejado:

- `PROJECT_STATE.md`;
- `ECOSYSTEM_REGISTRY.yaml`;
- `ARCHITECTURE.md`;
- `ROADMAP.md`;
- `RELEASE_MATRIX.md`;
- `AGENTS.md`;
- diretório de decisões/ADRs.

### G2 — Contratos e schemas compartilhados

Planejado, sem presumir implementação imediata:

- proveniência;
- fatos clínicos;
- fontes documentais;
- referências/evidência;
- reconciliação;
- eventos de auditoria;
- configuração multi-provider;
- versionamento e compatibilidade.

Contratos começam como especificações. Um kernel ou pacote compartilhado só deve ser extraído quando houver consumidores reais e testes de compatibilidade.

### G3 — Saúde automatizada do portfólio

Planejado:

- detectar repositórios sem README/estado;
- branches e PRs divergentes;
- workflows falhos;
- artefatos sem hash;
- documentação contraditória;
- gates pendentes;
- dependências incompatíveis;
- projetos sem próximo passo registrado.

### G4 — Integração progressiva

A integração entre produtos deve ocorrer por contratos versionados, não pela fusão prematura de HTMLs ou duplicação de lógica.

### G5 — Painel do ecossistema

Um painel futuro poderá mostrar estado, versão, bloqueadores, PRs, gates e links de cada produto. Ele será inicialmente um painel de governança, sem armazenar dados clínicos.

## Estrutura-alvo planejada

```text
RechHub/
├── README.md
├── PROJECT_STATE.md
├── AGENTS.md
├── ARCHITECTURE.md
├── ROADMAP.md
├── ECOSYSTEM_REGISTRY.yaml
├── RELEASE_MATRIX.md
├── decisions/
├── contracts/
├── schemas/
├── reports/
├── scripts/
├── tests/
└── .claude/
    └── skills/
```

A árvore acima é roadmap. Apenas arquivos realmente presentes no GitHub devem ser tratados como implementados.

## Política de mudanças

Antes de alterar uma skill ou contrato:

1. estabelecer o estado atual do repositório;
2. identificar a unidade de mudança;
3. distinguir FACT, INFERENCE, PROPOSAL e DECISION;
4. preservar invariantes e escopo;
5. criar evidência reproduzível;
6. registrar testes e limitações;
7. submeter a mudança aos gates aplicáveis;
8. atualizar o estado canônico quando necessário.

## Visão final

O RechHub deve funcionar como o **centro de comando e memória operacional do Ecossistema RECH**:

- cada produto permanece modular;
- cada domínio tem proprietário único;
- agentes seguem contratos explícitos;
- mudanças deixam evidência;
- regressões são verificadas;
- releases dependem de gates;
- integração ocorre somente após estabilização dos módulos e schemas.

O objetivo não é burocratizar o desenvolvimento. É permitir que o ecossistema cresça sem perder conteúdo, misturar autoridades, reabrir decisões encerradas ou declarar segurança sem evidência.
