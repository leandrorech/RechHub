# Registro de defeitos conhecidos

Os itens abaixo foram fornecidos como defeitos já reproduzidos numa
implementação anterior desta skill, não recuperável neste repositório. Cada
um foi endereçado nesta reconstrução com uma correção específica e um teste
que prova a correção — nenhum item aqui é fechado só por afirmação em prosa.

Numeração conforme a especificação original (11 itens); #1/#8 e #6/#11 são,
na prática, o mesmo requisito declarado duas vezes na fonte, então a matriz
final do relatório os trata como 10 linhas distintas.

## 1/8. EVAL_MANIFEST deve ser congelado/hasheado antes de qualquer run

**Correção**: `snapshot_manager.freeze()` grava uma cópia canônica em
`snapshot/eval_manifest.canonical.yaml`. `run_executor.py` só abre essa
cópia — nunca o arquivo de trabalho — e recusa (`RuntimeError`) rodar se ela
não existir.

**Teste**: `test_snapshot_manager.py::test_manifest_snapshot_created_before_run_executor_can_run`.

## 2. VALID_RUN_GATE não pode dar PASS com eval declarado faltando

**Correção**: `valid_run_gate.py` checa completude estrutural (todo eval
`required` presente) antes de ler qualquer outcome. Faltando um -> FAIL
imediato, run listada como estruturalmente incompleta na evidência.

**Teste**: `test_valid_run_gate.py::test_missing_required_eval_blocks_gate`.
Complementado por `test_stale_manifest_run_is_rejected` (uma run contra um
manifesto desde então re-congelado também é estruturalmente incompleta, não
só "eval faltando" no sentido estrito).

## 3. ARTIFACT_INTEGRITY_GATE deve proteger todos os decision inputs

**Correção**: `artifact_integrity_gate.py` roda o mesmo laço de
recomputar-e-comparar sobre as 6 categorias (`ORIGINAL`, `PREVIOUS`,
`CANDIDATE`, `EVAL_MANIFEST`, `CONTRACT`, `CONFIG`) mais
`EVAL_DEFINITIONS_FIXTURES`, sem nenhum código especial para `CANDIDATE`.

**Teste**: `test_artifact_integrity_gate.py::test_integrity_covers_all_named_inputs`
(parametrizado sobre as 5 categorias mutáveis nesta suíte; cada mutação
isolada é detectada e nomeada corretamente, e só ela).

## 4. SKILLS_API não pode dar PASS vazio

**Correção**: `skills_api_validate.py` retorna uma lista de checks, cada um
com `status` + `detail` não-vazio. Checks genuinamente fora de escopo
offline (`upload_registration`, `live_routing`) são sempre
`NOT_APPLICABLE`, nunca omitidos nem promovidos a `PASS`. `overall_status()`
nunca retorna `PASS` enquanto houver algum `UNVERIFIED`.

**Teste**: `test_skills_api_validate.py::test_no_bare_pass_without_evidence`
e `test_missing_skills_root_yields_partial_not_pass`.

## 5. contract_template deve ser o contrato completo aprovado

**Correção**: `contract_template.yaml` contém todas as chaves listadas em
`schema_validator.REQUIRED_TOP_LEVEL_KEYS`, verificado mecanicamente, não só
por inspeção visual.

**Teste**: `test_schema_validator.py::test_contract_template_matches_required_key_set`.

## 6/11. PACKAGE_RELEASE_GATE exige os dois gates, sem ambiguidade de nome

**Correção**: `package_release_gate()` só retorna `RELEASABLE` se
`VALID_RUN_GATE` e `ARTIFACT_INTEGRITY_GATE` PASSarem os dois. O
identificador `release_gate` nunca aparece sozinho no módulo — sempre
`package_release_gate`, evitando colisão conceitual com o skill irmão
`rech-release-gate` (release de produto RECH, não de pacote de skill).

**Testes**: `test_package_release_gate.py::test_blocked_without_valid_run_gate_pass`,
`test_blocked_without_artifact_integrity_gate_pass`, e
`test_no_naming_ambiguity` (varredura AST, não promessa em docstring).

## 7. EVAL_ISOLATION nunca PASSa com --scope ausente

**Correção**: `eval_isolation_check.py` retorna `UNVERIFIED` se `--scope`/
`--scope-file` foi omitido ou resolveu para zero evals, e `PARTIAL` se o
escopo cobre só parte dos evals obrigatórios ou tem overlap de recurso
compartilhado detectado. `PASS` só é alcançável com escopo explícito,
completo e sem overlap.

**Testes**: `test_eval_isolation_check.py::test_missing_scope_yields_unverified_not_pass`
e `test_insufficient_scope_yields_partial_not_pass`.

## 9. Schema deve aceitar o campo metadata

**Correção**: `metadata` está em `REQUIRED_TOP_LEVEL_KEYS`; `schema_validator.py`
valida que é um mapeamento quando presente e reporta erro nomeando `metadata`
quando ausente.

**Testes**: `test_schema_validator.py::test_metadata_field_accepted` e
`test_metadata_missing_is_rejected`.

## 10. package_validate deve parsear YAML multiline corretamente

**Correção**: todo parsing de YAML no pacote passa exclusivamente por
`rsc_common.load_yaml()`/`load_yaml_str()` (PyYAML `safe_load`) — nenhum
scanner de linha próprio em nenhum lugar, incluindo o parser de frontmatter
do `SKILL.md`.

**Teste**: `test_package_validate.py::test_multiline_block_scalar_parsed_correctly`
— um block scalar `|` com uma linha-isca que parece uma chave YAML real
(`assertions: ...`) é confirmado como texto literal, nunca promovido a
estrutura de documento.

## Observação sobre integridade adicional (não numerada na lista original)

Durante a implementação, um gap real foi encontrado e corrigido além da
lista original: `valid_run_gate.py` não checava se o `manifest_sha256`
gravado numa run batia com o manifesto atualmente congelado — uma run
executada contra um manifesto antigo (desde então re-congelado) podia, em
tese, ser aceita mesmo não representando mais uma execução válida contra o
contrato atual. Corrigido: toda run agora é rejeitada como estruturalmente
incompleta ("stale") se seu `manifest_sha256` não bater com o snapshot
vigente. Ver `test_valid_run_gate.py::test_stale_manifest_run_is_rejected`.
