# Domain profiles

As camadas de metodologia são a única parte desta skill que diverge por domínio. Todo o resto (input contract, evidence model, finding model, severity/confidence/status, scope/coverage, output contract) é compartilhado — ver `SKILL.md`.

## CODE — 8 camadas

Percorra nesta ordem. Não pule camadas mesmo que as primeiras pareçam "limpas" — problemas em camadas mais profundas frequentemente só aparecem depois de mapear as superficiais.

1. **Sintaxe/Compilação** — erros que quebram build/parse. Rode o compilador/linter real se disponível e seguro (ver `execution-policy.md`).
2. **Lógica local** — bugs dentro de uma função/módulo isolado: off-by-one, condições invertidas, null/undefined não tratado, comparação de tipo errada, funções ausentes que deveriam existir.
3. **Integração/Contrato** — dados errados entre módulos: função retorna X mas quem chama espera Y; schema de storage vs o que o código grava; parâmetros inconsistentes entre frontend/backend.
4. **Estado e concorrência** — condições de corrida, estado mutável inconsistente, duplicação de dados, storage fora de sincronia com a UI, race conditions em chamadas assíncronas.
5. **Arquitetura/Design** — acoplamento indevido, responsabilidades mal distribuídas, decisões que geram dívida técnica, violação de padrões já estabelecidos no projeto.
6. **Segurança** — XSS, injeção (SQL/command), dados sensíveis expostos, chaves de API hardcoded, falta de sanitização de input do usuário.
7. **Performance** — complexidade algorítmica desnecessária, re-renders/recomputações evitáveis, queries sem índice, memory leaks.
8. **Consistência com o ecossistema** — o código novo contradiz padrões, convenções ou decisões já tomadas em outras partes do projeto ou de projetos irmãos RECH?

## CONTENT — 4 camadas

1. **Consistência interna** — o documento se contradiz entre seções (ex.: uma tabela diz uma dose, o texto diz outra)?
2. **Precisão factual/técnica ou clínica** — verificar contra conhecimento técnico/clínico estabelecido. Exige fonte identificável (ver regra em `finding-schema-and-raf-mapping.md`: nunca confirmar por memória do modelo sozinha).
3. **Consistência com guidelines/fontes de referência** — alinhamento com KDIGO, Surviving Sepsis, AHA/ACC/ESC, GOLD, SBC, AMIB/SBI, ou a fonte normativa aplicável ao domínio do documento.
4. **Estrutura/completude** — lacunas, seções incompletas, referências cruzadas quebradas, inconsistência de formatação/nomenclatura ao longo do documento.

## MIXED

Aplique os dois perfis **separadamente**, sobre as partes correspondentes do `AUDIT TARGET`. Nunca misture evidência metodologicamente distinta dentro do mesmo finding — um finding é sempre `DOMAIN: CODE` ou `DOMAIN: CONTENT`, nunca os dois ao mesmo tempo, mesmo quando o `AUDIT TARGET` combina ambos (ex.: um módulo de código com documentação clínica embutida). Consolide ao final num resumo único, mas mantendo a proveniência de domínio de cada finding individual rastreável.

## Notas de aplicação (herdadas da v1, ainda válidas)

- Se o projeto já tem convenções conhecidas (ex.: vanilla JS/TS single-file, sem bundler), leve isso em conta na camada 8 (CODE) — não sugira mudanças de arquitetura que quebrem o padrão do projeto sem justificativa forte. Isso é informação que `rech-repo-context`, quando `REQUIRED`/`RECOMMENDED`, já pode fornecer como `HARD CONSTRAINT`/`CURRENT CONSTRAINT` descoberto.
- Em documentos clínicos, trate "precisão factual" com rigor bayesiano/quantitativo: cite a fonte/guideline quando apontar um erro factual, não apenas afirme que está errado.
- Para escopos grandes, se a varredura completa das camadas for inviável em uma resposta só, comunique isso explicitamente (`PARTIALLY_AUDITED`) e proponha dividir por módulo/arquivo, mantendo a mesma estrutura de camadas em cada parte — nunca comprometa a promessa de cobertura silenciando a divisão.
