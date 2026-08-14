# Quando pular a Aprovação 1 (pré-fix) é aceitável

Padrão no ecossistema RECH: sempre pedir aprovação pré-fix, mesmo para correções que parecem óbvias. A exceção só existe para reduzir atrito em casos genuinamente triviais, e mesmo assim é uma decisão do Leandro, não algo que a skill infere sozinha na primeira vez.

Pular a Aprovação 1 só é aceitável quando **todas** as condições abaixo são verdadeiras:

- o fix é local a uma única função pura, sem efeito colateral em outros componentes;
- não toca em nenhum invariante, contrato ou spec documentado;
- não muda comportamento observável do sistema do ponto de vista clínico ou de dado (ex.: typo em mensagem de log, correção de off-by-one isolado confirmado por teste determinístico);
- severidade é LOW;
- o usuário já sinalizou, nesta conversa ou em instrução permanente, que aceita esse nível de autonomia para este tipo de caso.

Se qualquer uma dessas condições não for clara, peça a Aprovação 1 normalmente — o custo de perguntar é baixo; o custo de aplicar uma mudança não autorizada em código clínico não é.

Mesmo quando a Aprovação 1 é pulada, o relatório completo (causa raiz, baseline, teste, registro de mudança) continua obrigatório. O que muda é só a pausa para autorização explícita antes de tocar em código — a rastreabilidade não é opcional em nenhum cenário.

---

# Árvore de decisão — TESTABILITY

```
O comportamento pode ser verificado por um teste automatizado determinístico
(unitário, integração, ou E2E via Playwright/similar)?
│
├─ SIM → TESTABILITY: FULL
│         Siga o ciclo RED → fix → GREEN → suíte relacionada → suíte completa.
│
└─ NÃO → o comportamento é visual, estrutural, ou de output complexo
          (ex.: layout de documento, DOCX gerado, PDF, formatação)?
          │
          ├─ SIM, e existe golden case/fixture aplicável
          │   → use comparação estrutural contra o golden case.
          │     TESTABILITY: LIMITED (mitigada por golden case)
          │
          ├─ SIM, e NÃO existe golden case/fixture ainda
          │   → considere criar um golden case como parte do fix,
          │     se o esforço for proporcional ao risco do bug.
          │     Se não for viável agora, registre:
          │     TESTABILITY: LIMITED
          │     AUTOMATED REGRESSION TEST: NOT AVAILABLE
          │     REASON: sem golden case/fixture disponível
          │     ALTERNATIVE VERIFICATION: <snapshot manual, comparação
          │       visual documentada, smoke test reproduzível>
          │
          └─ NÃO é visual/estrutural, mas ainda assim não há infraestrutura
              de teste no projeto para esse tipo de comportamento
              → TESTABILITY: LIMITED
                AUTOMATED REGRESSION TEST: NOT AVAILABLE
                REASON: <infraestrutura ausente para este tipo de verificação>
                ALTERNATIVE VERIFICATION: <o que foi feito no lugar,
                  suficientemente descrito para ser reproduzido por outra
                  pessoa/sessão sem ambiguidade>
```

Regra dura em qualquer ramo: nunca declarar `TESTABILITY: FULL` ou marcar um teste como cobrindo o bug se, na prática, o teste não reproduz de forma confiável o cenário que causava o problema. Um teste que passa por acidente (não porque testa a condição certa) é pior do que nenhum teste, porque cria falsa confiança em `rech-regression-guardian` nas próximas execuções.
