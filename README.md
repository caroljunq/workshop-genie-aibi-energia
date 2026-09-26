# Workshop Databricks — Genie + AI/BI

Guia para um time de energia: criar tabelas no Unity Catalog, configurar um
Genie Agent, montar um dashboard com Genie Code (gráficos e mapas), definir
KPIs governados em uma metric view e, se quiser, criar uma Custom Visualization
Vega-Lite.

Todos os nomes e dados são sintéticos. Nenhuma empresa real é mencionada.

---

## Estrutura

```text
.
├── README.md
├── notebook_guia_workshop.ipynb
└── dados/
    ├── ativos_geo.csv
    ├── medicoes_horarias.csv
    ├── eventos_operacionais.csv
    └── rotas_inspecao.csv
```

O `notebook_guia_workshop.ipynb` contém todo o passo a passo. A pasta `dados/`
já está no workspace; o Módulo 1 cria as tabelas a partir desses CSVs.

---

## Módulos

| Módulo | Tema | Resultado |
|---:|---|---|
| 1 | Criar tabelas com SQL | Quatro tabelas no Unity Catalog |
| 2 | Genie best practices | Agent pequeno e bem curado |
| 3 | Laboratório Genie | Perguntas e SQL revisados |
| 4 | AI/BI com Genie Code | Dashboard com gráficos e mapas |
| 5 | Genie One | Exploração assistida dos dados |
| 6 | Vega-Lite (opcional) | Custom Viz de disponibilidade |
| 7 | Importar BI (opcional) | Visão do fluxo `/importBI` |
| 8 | Metric view de operação | KPIs governados de geração, carga, disponibilidade e fator de capacidade |

O Módulo 8 fecha o roteiro com uma camada semântica reutilizável pelo Genie e
pelo AI/BI. Ele cria `{prefixo}_mv_operacao` sobre
`{prefixo}_medicoes_horarias`, com um relacionamento *many-to-one* para
`{prefixo}_ativos_geo`. Assim, regras como “disponibilidade deve ser calculada
por média, nunca por soma” ficam definidas uma única vez.

---

## Modelo de dados

O workshop usa exatamente quatro tabelas. Todas as fatos se ligam a
`ativos_geo` por `ativo_id`.

| CSV | Tabela | Conteúdo |
|---|---|---|
| `ativos_geo.csv` | `{prefixo}_ativos_geo` | Ativos, capacidade, estado e coordenadas |
| `medicoes_horarias.csv` | `{prefixo}_medicoes_horarias` | Geração, carga e disponibilidade |
| `eventos_operacionais.csv` | `{prefixo}_eventos_operacionais` | Severidade, duração e impacto |
| `rotas_inspecao.csv` | `{prefixo}_rotas_inspecao` | Pontos ordenados para path map |

```text
ativos_geo (ativo_id)
   ├──< medicoes_horarias (ativo_id)
   ├──< eventos_operacionais (ativo_id)
   └──< rotas_inspecao (ativo_id)
```

Use um prefixo individual nos widgets (`seu_prefixo`) para não sobrescrever
a tabela de outro participante.

---

## Como usar

1. Abra `notebook_guia_workshop` no Databricks.
2. Preencha os widgets: catálogo, schema, prefixo e caminho da pasta `dados`.
3. Rode a célula dos widgets e, em seguida, as células SQL do Módulo 1.
4. Se o `read_files` falhar, use o upload manual descrito no mesmo módulo.
5. Siga Genie, dashboard e mapas na ordem. Vega-Lite e importação de BI são
   opcionais.
6. No Módulo 8, execute o SQL que cria
   `{seu_prefixo}_mv_operacao` e valide as medidas com `MEASURE()`.
7. Adicione a metric view ao Genie Agent para perguntas de KPI. Continue usando
   `ativos_geo` e `rotas_inspecao` diretamente para mapas, pontos e rotas.

Células Python dos Módulos 2, 4 e 5 imprimem textos já preenchidos
(pergunta, SQL, prompts do Genie Code). Rode a célula **antes** de copiar:
os `${widgets}` só viram nomes reais na execução.

---

## Pré-requisitos

- Unity Catalog
- SQL Warehouse Pro ou Serverless
- permissão para criar schema e tabelas
- Genie Agents e Genie Code habilitados
- AI/BI Dashboards
- Custom Viz para o exercício Vega-Lite (opcional)
- Metric views (Databricks Runtime 17.3+ recomendado) para o Módulo 8

---

## Referências

- [Genie best practices](https://docs.databricks.com/aws/en/genie/best-practices)
- [Create and manage a Genie Agent](https://docs.databricks.com/aws/en/genie/set-up)
- [Genie Code for dashboards](https://docs.databricks.com/aws/en/dashboards/manage/dashboard-agent)
- [AI/BI visualization types](https://docs.databricks.com/aws/en/dashboards/manage/visualizations/types)
- [Vega-Lite custom visualizations](https://docs.databricks.com/aws/en/dashboards/manage/visualizations/custom-visualizations)
- [Import BI files with Genie Code](https://docs.databricks.com/aws/en/dashboards/manage/import-bi)
- [Unity Catalog metric views](https://docs.databricks.com/aws/en/uc-semantics/metric-views/)
- [Create a metric view](https://docs.databricks.com/aws/en/uc-semantics/metric-views/create)
