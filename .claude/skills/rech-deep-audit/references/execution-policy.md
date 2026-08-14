# Execution policy

Diferente de `rech-repo-context` (zero execução de código do projeto, sempre), `rech-deep-audit` pode legitimamente precisar executar verificações — reproduzir um bug, rodar um linter, confirmar um comportamento — porque parte do seu trabalho é elevar a classe de evidência de um finding (ver `finding-schema-and-raf-mapping.md`, E1→E4 normalmente exige alguma forma de execução/reprodução).

## Default: SAFE / NON-DESTRUCTIVE EXECUTION

Permitido quando apropriado ao finding sendo investigado:

```
- static analysis (ex.: análise de padrões sem executar o código)
- linters
- compiler/check (ex.: cargo check, tsc --noEmit)
- testes isolados conhecidos como seguros (ex.: testes unitários puros,
  sem dependência de rede/API externa)
- diagnósticos read-only (ex.: inspecionar output de um comando sem
  efeito colateral)
```

## Nunca executar cegamente

```
- chamadas de API reais — RISCO ESPECÍFICO DO RECH: vários projetos
  (RechDocs, RechStudy, RechSupps) fazem chamadas client-side a múltiplos
  provedores de IA (Anthropic, OpenAI, Gemini, DeepSeek, Qwen). Rodar um
  fluxo que dispara isso "só para confirmar um finding" tem custo e
  efeito colateral reais, não é uma verificação neutra.
- chamadas de rede com custo
- migrations
- escrita em banco de dados
- acesso a produção
- deploy
- comandos dependentes de credenciais
- scripts com efeito colateral desconhecido (se não está claro o que um
  script faz, não rode "para ver o que acontece")
- fluxos de browser que mutam estado externo
```

## Protocolo quando há risco

```
STOP
  → explique o risco especificamente (o que poderia acontecer, não
    genericamente "pode ter efeito colateral")
  → peça autorização explícita, OU
  → use uma alternativa seguramente equivalente se existir (ex.: análise
    estática do código da chamada de API em vez de disparar a chamada
    de verdade; leitura do schema de teste em vez de rodá-lo se o teste
    tiver setup que popula/consome recursos reais)
```

## Regra dura

A skill pode executar **para observar**. Nunca modifica o alvo para influenciar o resultado da própria auditoria — nem mesmo como parte de uma verificação aparentemente legítima ("vou só ajustar esse valor pra testar" não é uma exceção válida; isso deixaria de ser auditoria read-only e viraria experimentação não autorizada no código de produção).

Se a execução seria necessária para confirmar um finding, mas o risco não pode ser mitigado com segurança e a autorização não foi obtida: o finding permanece em `STATUS: PLAUSIBLE` (ou `INCONCLUSIVE`, se a evidência disponível sem execução for muito fraca) — nunca force a execução só para poder declarar `CONFIRMED`.
