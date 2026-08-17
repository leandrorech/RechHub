# Semântica dos três gates

## VALID_RUN_GATE

Implementação: `scripts/valid_run_gate.py`.

```
1. Se o manifesto não estiver congelado (snapshot_manager.freeze() nunca
   rodou) -> FAIL imediato.
2. Descobrir run-N/ em disco (nunca sintetizado).
3. Sem nenhuma run -> FAIL ("no runs found").
4. Para cada run, checar completude ESTRUTURAL, nesta ordem:
   a. run_meta.json existe e seu manifest_sha256 bate com o do snapshot
      ATUAL -> senão, run é "stale" (rodou contra um manifesto antigo,
      re-congelado desde então) -> estruturalmente incompleta.
   b. todo eval_id `required: true` do manifesto congelado tem um
      result.json sob essa run -> senão, estruturalmente incompleta,
      nomeando os evals faltantes.
5. Qualquer run estruturalmente incompleta (por eval faltante OU por
   manifesto obsoleto) -> FAIL do gate inteiro, antes de qualquer outcome
   ser sequer lido.
6. Entre as runs estruturalmente completas, uma run é "válida" se nenhum dos
   seus evals obrigatórios voltou RUN_INVALID. RUN_INVALID nunca conta como
   PASS nem como FAIL funcional — só remove a run do pool de válidas.
7. Se o número de runs válidas < min_valid_runs (default 1, configurável via
   --min-valid-runs) -> FAIL ("insufficient valid runs").
8. Entre as runs válidas, PASS só se TODO eval obrigatório em TODA run
   válida tiver outcome PASS. Qualquer FAIL funcional -> FAIL do gate.
```

`primary`/`baseline_ref` nunca são lidos por posição em lista — sempre pelos
campos explícitos do manifesto.

## ARTIFACT_INTEGRITY_GATE

Implementação: `scripts/artifact_integrity_gate.py`.

```
1. snapshot/decision_input_manifest.json não existe -> FAIL ("no snapshot
   found").
2. Para CADA uma das 6 categorias (ORIGINAL, PREVIOUS, CANDIDATE,
   EVAL_MANIFEST, CONTRACT, CONFIG) mais a lista EVAL_DEFINITIONS_FIXTURES —
   MESMO laço, sem nenhum caso especial para CANDIDATE:
     a. recomputar (kind, sha256) do path gravado, usando a MESMA função de
        hash usada no freeze (rsc_common.hash_path_smart — uma única
        implementação, importada, nunca reimplementada aqui).
     b. se o kind gravado era != "none" e o kind atual é "none" -> MISSING.
     c. se o hash recomputado != hash gravado -> CHANGED.
3. Qualquer CHANGED ou MISSING -> FAIL, com a lista completa de
   categoria/path/hash-antigo/hash-novo como evidência — nunca um booleano
   solto.
4. Nenhum problema em nenhuma categoria -> PASS.
```

Diretórios são hasheados como árvore Merkle-lite (`relpath:sha256(bytes)`
por arquivo, ordenado, tudo junto hasheado) — nunca hash de tarball, que
embutiria metadata (mtime/uid/permissões) e geraria falso positivo numa
checkout limpa com conteúdo idêntico. Arquivos YAML/JSON são canonicalizados
antes do hash (edição cosmética não muda o hash; mudança de valor real
sempre muda).

## PACKAGE_RELEASE_GATE

Implementação: `scripts/package_release_gate.py`.

```
package_release_gate(valid_run_gate_result, artifact_integrity_gate_result):
  se algum dos dois resultados for None -> INCONCLUSIVE
    (o gate não conseguiu nem ser calculado, diferente de ter sido
    calculado e dado FAIL)
  se VALID_RUN_GATE != PASS -> BLOCKED, citando VALID_RUN_GATE
  se ARTIFACT_INTEGRITY_GATE != PASS -> BLOCKED, citando ARTIFACT_INTEGRITY_GATE
  senão -> RELEASABLE
```

`RELEASABLE` (não `READY`) e o nome sempre por extenso `PACKAGE_RELEASE_GATE`
(nunca abreviado para `release_gate`) são escolhas deliberadas de distância
léxica do skill irmão `rech-release-gate`, que decide uma coisa
completamente diferente (release de produto RECH, não empacotamento de
skill). `test_no_naming_ambiguity` garante isso mecanicamente via `ast`.

## Regra comum às três: SEVERITY ⟂ GATE

Nenhum dos três gates usa "severidade" de nada para decidir PASS/FAIL/
BLOCKED por si só. Cada um tem sua própria lógica binária/composta explícita,
descrita acima — severidade (quando aparece em algum finding relacionado) é
sempre um eixo separado, nunca o que decide o veredito do gate.
