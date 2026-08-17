# Esquema do contrato — campo a campo

Fonte canônica: `contract_template.yaml` (a versão executável/validável deste
documento — `schema_validator.py` valida contra a constante
`REQUIRED_TOP_LEVEL_KEYS`, que espelha exatamente as chaves de topo abaixo).

Nenhum campo de classificação aqui usa vocabulário próprio — `severity` e
`minimum_evidence_level` são sempre da escala RAF (ver
`rech-deep-audit/references/finding-schema-and-raf-mapping.md`).

## Chaves de topo obrigatórias

| Chave | Tipo | Descrição |
|---|---|---|
| `skill_id` | string (kebab-case) | Deve bater com o nome do diretório. |
| `name` | string | Deve bater com `name` do frontmatter do `SKILL.md`. |
| `version` | string | Versão semântica da skill. |
| `goal` | string (block scalar) | 1-3 frases: a pergunta única que a skill responde. |
| `when_to_use` | mapping | `triggers[]` e `negative_triggers[]` (cada um com `pattern` + `redirect_to`). |
| `input_contract` | mapping | `required_fields[]` / `optional_fields[]`, cada campo com `name`/`type`/`description`. |
| `output_contract` | mapping | `format` (`structured-fields`\|`markdown-report`\|`json`) + `required_fields[]`. |
| `skill_schema` | mapping | `frontmatter_fields` (travado em `["name","description"]`), `description_max_chars` (1024), `body_sections[]`. |
| `execution_environment` | mapping | `requires_code_execution`, `execution_boundary` (`read-only`\|`safe-non-destructive`\|`full`), `network_access`, `external_dependencies[]`. |
| `risk_side_effects` | array | Cada item: `description` + `mitigation`. |
| `hard_constraints` | array de string | Regras que nunca podem ser violadas. |
| `preferred_constraints` | array de string | Regras seguidas na ausência de exceção documentada. |
| `current_constraints` | array de string | Limitações da implementação atual. |
| `non_goals` | array de string | O que a skill deliberadamente não faz. |
| `invariants` | array | Reusa IDs `INV-`/`CAP-`/`SAFE-`/`REG-<PROJETO>-<ÁREA>-<N>` de `rech-regression-guardian/references/invariants-format.md`. Cada item: `id`, `description`, `severity` (RAF), `status` (`approved`\|`candidate`). |
| `failure_modes` | array | Cada item: `description`, `detection`, `severity` (RAF). |
| `evidence_required` | array | Cada item: `field`, `minimum_evidence_level` (RAF `E0`-`E5`). |
| `metadata` | mapping | `owner`, `created`, `last_reviewed`, `status` (`draft`\|`proposed`\|`approved`\|`locked`), `tags[]`, `related_skills[]`, `extra` (bag aberto). Aceito e validado por `schema_validator.py` (defeito #9). |

## Regras de validação (`schema_validator.py`)

1. Toda chave de topo listada acima deve estar presente. Falta de qualquer
   uma → erro nomeando a chave.
2. `metadata` deve ser um mapeamento (não string, não lista, não nulo).
3. Qualquer `severity` em `invariants[]`/`failure_modes[]` deve estar em
   `{BLOCKER, CRITICAL, HIGH, MEDIUM, LOW}` — fora disso é erro.
4. Qualquer `minimum_evidence_level` em `evidence_required[]` deve estar em
   `{E0, E1, E2, E3, E4, E5}` — fora disso é erro. `E0`/`E5` são aceitos mas
   geram um **warning** (não erro) citando que não são textualmente
   confirmados por RAF, só usados "no espírito da escala".

## O que este documento NÃO faz

Não define um vocabulário de severidade/confiança/status próprio da skill.
Onde uma classificação é necessária, ela aponta para RAF — nunca duplica ou
substitui.
