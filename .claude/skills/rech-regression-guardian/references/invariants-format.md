# Formato de RECH_INVARIANTS.md

Este arquivo, quando existe na raiz de um projeto RECH, é a fonte de evidência de maior confiança (nível 1 da hierarquia). Ele documenta contratos do sistema que não podem ser violados, independentemente de refatoração, correção ou migração.

## Convenção de IDs

- `INV-<PROJETO>-<ÁREA>-<NÚMERO>` — invariante (ex.: `INV-RD-VENT-003` = RechDocs, Ventilação, item 3)
- `CAP-<PROJETO>-<ÁREA>-<NÚMERO>` — capability (funcionalidade que deve seguir acessível)
- `SAFE-<PROJETO>-<ÁREA>-<NÚMERO>` — safeguard (mecanismo de proteção)
- `REG-<PROJETO>-<ÁREA>-<NÚMERO>` — regressão conhecida já registrada em algum momento (útil para não reintroduzir o mesmo bug)

Prefixos de projeto sugeridos: `RD` (RechDocs), `RS` (RechStudy), `RSP` (RechSupps), `RT` (RechTrauma), `RSH` (RechShift).

## Template de entrada

```
## INV-RD-VENT-003
Após evento de extubação, parâmetros ventilatórios do episódio
anterior não podem ser propagados para episódio subsequente.

Severity: CRITICAL
Component: ClinicalState / resolveVentilatorio()
Applies to: RechDocs
Approved: <data ou contexto de aprovação>
Evidence at creation: RAF-017, teste tests/clinicalstate/vent.test.ts
```

Campos:
- **Severity**: CRITICAL / HIGH / MEDIUM / LOW. CRITICAL é reservado para invariantes clínicos cuja violação pode causar dano direto (perda de proveniência, mistura de episódios, informação não confirmada virando fato clínico).
- **Component**: função, módulo ou arquivo onde o invariante se aplica — ajuda a decidir se um diff toca nele.
- **Applies to**: projeto(s) RECH.
- **Approved**: quando/como foi aprovado — evita invariantes "fantasmas" que ninguém confirmou de fato.
- **Evidence at creation**: por que esse invariante existe (finding RAF, bug corrigido, decisão de design). Rastreabilidade histórica.

## Candidate invariants (nível B da skill)

Quando a skill sugere promover um padrão observado a invariante oficial, registre separadamente, nunca direto na lista de invariantes aprovados:

```
## CANDIDATE — não promovido
Sugestão: resolveVentilatorio() não deve propagar parâmetros após extubação.
Evidência: finding RAF-017, commit abc123, teste tests/clinicalstate/vent.test.ts
Confiança: alta
Status: aguardando decisão do Leandro
```

Só migra para a seção de invariantes aprovados quando o Leandro confirmar explicitamente — a skill nunca promove sozinha.

## Exemplos reais já conhecidos do ecossistema (referência, não exaustivo)

Estes já apareceram em auditorias anteriores e são bons candidatos a formalizar em RECH_INVARIANTS.md quando o projeto ainda não os tem documentados:

- RechDocs: parâmetros ventilatórios não podem vazar entre episódios de extubação (P0 confirmado em v3.4.1).
- RechDocs: estados ventilatórios conflitantes/simultâneos não podem ser resolvidos silenciosamente sem alerta bloqueante (P0 confirmado em v3.4.1).
- RechDocs: ClinicalState não pode perder proveniência de dado (cada item deve manter rastreabilidade da origem).
- RechShift: cada item de reconciliação (ReconciliationItem) deve manter proveniência tipada por item.
