# Constraint model — rech-github-scout

Três categorias, nunca fundidas em uma escala única e nunca combinadas em
score numérico:

```
HARD                — critério eliminatório.
PREFERRED            — desejável, não eliminatório.
CURRENT CONSTRAINT   — limitação factual atual, potencialmente mutável.
```

## HARD

Falha em `HARD` elimina `ADOPT` e normalmente também elimina `ADAPT` (um
`ADAPT` só sobrevive a uma violação `HARD` se a adaptação necessária
resolver exatamente essa violação — nunca se a violação permanecer após a
adaptação proposta).

Exemplos, quando aplicáveis ao caso:

```
- licença incompatível com o uso pretendido
- exige cloud quando offline é requisito obrigatório
- runtime incompatível com o stack do RECH
- dependência proibida por política já declarada
- requisito regulatório obrigatório ausente no candidato
- arquitetura incompatível de forma estrutural (não contornável por
  configuração/adaptação razoável)
```

**Regra central:** `HARD failure cannot be averaged away.` Um candidato com
ótimo fit funcional, ótima manutenção e ótima licença, mas que falha em uma
única `HARD constraint`, continua `ELIMINATED`. Não existe pontuação
agregada 0–100 que "compense" uma violação `HARD` nesta v1 — ver
`SKILL.md` § "Overengineering guard".

`HARD` só é registrada com base em:
- constraint explicitamente declarada no input (`HARD CONSTRAINTS` do
  `INPUT CONTRACT`), ou
- evidência textual explícita de um documento formal do RECH (invariante,
  ADR), obtida via `rech-repo-context` quando `REPO CONTEXT: REQUIRED`.

Nunca inventada por inferência da skill a partir de "parece razoável que
isso seja obrigatório".

## PREFERRED

Usado exclusivamente para ranquear candidatos que já sobreviveram ao filtro
`HARD` (etapa 5 do pipeline, `HARD-CONSTRAINT FILTER`). Uma preferência não
satisfeita nunca elimina um candidato — no máximo o posiciona pior na
`COMPARE` (etapa 8).

## CURRENT CONSTRAINT

Limitação factual do estado atual do RECH, que pode mudar sem que isso
represente violar nenhuma regra deliberada. Exemplo: "hoje o RECH não tem
backend" é uma `CURRENT CONSTRAINT` — descreve o estado presente, não uma
proibição.

**Nunca promover automaticamente:**

```
"hoje não existe backend"        (CURRENT)
        ↓ NUNCA vira, por conta própria
"backend é proibido"             (HARD)
```

Promover `CURRENT` a `HARD` exige a mesma evidência textual explícita
exigida para qualquer `HARD` — nunca a mera observação de que o estado
atual não suporta algo. Fazer essa promoção sem evidência é uma das
condições de `HARD ACCEPTANCE FAIL` (ver `acceptance-cases.md`, caso 14).

## UNKNOWN

Quando o input não declara uma constraint e nenhuma fonte inspecionável
permite inferi-la com segurança, ela é registrada como `UNKNOWN` — nunca
omitida silenciosamente, nunca preenchida por suposição plausível.

## Algoritmo de resolução (etapa 2 do pipeline — RESOLVE CONSTRAINTS)

1. Ler `HARD CONSTRAINTS` / `PREFERRED CONSTRAINTS` / `CURRENT CONSTRAINTS`
   declaradas no input; registrar cada uma na categoria informada.
2. Se `REPO CONTEXT` foi fornecido (ou é `REQUIRED` e foi obtido), extrair
   `HARD CONSTRAINTS` adicionais só de evidência textual explícita
   (invariantes/ADRs), nunca de observação de ausência estrutural isolada
   — isso último vira `CURRENT CONSTRAINT`, seguindo a mesma regra que
   `rech-repo-context` usa no seu próprio "Passo 7 — Constraint model".
3. Qualquer menção a limitação do RECH que não venha acompanhada de
   evidência textual explícita de que é deliberada é registrada como
   `CURRENT CONSTRAINT`, nunca `HARD`, por default.
4. Constraints mencionadas na conversa mas não claramente categorizáveis
   pelo usuário → perguntar ou registrar como `UNKNOWN` explicitamente,
   nunca resolver por conta própria a favor de uma leitura mais permissiva
   ou mais restritiva.
