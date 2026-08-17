# SKILLS_API — escopo checável offline

Implementação: `scripts/skills_api_validate.py`. Nunca retorna `PASS` vazio
(defeito #4) — todo check é `PASS`/`FAIL`/`UNVERIFIED`/`NOT_APPLICABLE` com
evidência não-vazia.

## Checável offline (sem rede)

| Check | O que verifica |
|---|---|
| `skill_md_present`, `frontmatter_parseable`, `frontmatter_required_fields` | Herdados de `package_validate.py` — `SKILL.md` existe, frontmatter parseia, `name`+`description` presentes. |
| `description_length` | `len(description) <= 1024`. |
| `description_charset` | UTF-8 válido, imprimível, sem caracteres de controle. |
| `naming_rules` | Nome do diretório casa `^[a-z0-9]+(-[a-z0-9]+)*$`. |
| `frontmatter_name_matches_dir` | `name` do frontmatter bate com o nome do diretório do pacote. |
| `references_only_md`, `scripts_only_py`, `no_stray_hidden_files` | Regras de tipo de arquivo por pasta. |
| `yaml_well_formed:<arquivo>` | Todo `*.yaml`/`*.yml` do pacote parseia via `yaml.safe_load`. |
| `internal_link_check` | Todo `redirect_to` em `when_to_use.negative_triggers` do `contract.yaml` resolve para um diretório irmão real (ou é `"none"`). Exige `--skills-root`; sem ele, `UNVERIFIED`. |

## Nunca checável neste sandbox — sempre `NOT_APPLICABLE`, nunca `PASS`

| Check | Por quê |
|---|---|
| `upload_registration` | Exige chamada de rede real à Skills API. |
| `live_routing` | Exige uma sessão Claude real escolhendo entre skills concorrentes. |
| `size_report` | Reportado como fato (bytes totais), mas não há constante real de limite documentada neste sandbox para pontuar contra — não é um gap transitório que mais input resolveria, é estruturalmente fora de escopo aqui, igual a uma chamada de rede. |

## Cálculo do status geral (`overall_status`)

```
se algum check == FAIL       -> FAIL
senão se algum check == UNVERIFIED -> PARTIAL
senão                          -> PASS
```

`FAIL` tem precedência sobre tudo. Qualquer `UNVERIFIED` (algo que
genuinamente não pôde ser checado, tipicamente por faltar `--skills-root`)
impede um `PASS` limpo — é o mecanismo concreto que impede o defeito #4:
um item `UNVERIFIED` nunca é silenciosamente absorvido num `PASS` geral.
`NOT_APPLICABLE` não bloqueia `PASS` por si só, porque está genuinamente
fora do escopo checável offline, não é uma lacuna que mais input resolveria.
