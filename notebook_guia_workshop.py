# Databricks notebook source
# MAGIC %md
# MAGIC # Workshop Databricks — Genie + AI/BI
# MAGIC ## Guia passo a passo
# MAGIC
# MAGIC
# MAGIC | Módulo | Resultado |
# MAGIC |---|---|
# MAGIC | Criar tabelas com SQL | Quatro tabelas no Unity Catalog |
# MAGIC | Genie best practices | Agent pequeno e bem curado |
# MAGIC | Laboratório Genie | Perguntas e SQL revisados |
# MAGIC | AI/BI com Genie Code | Dashboard com gráficos e mapas |
# MAGIC | Vega-Lite | Custom Viz de disponibilidade |
# MAGIC | Importar BI (opcional) | Visão do fluxo `/importBI` |
# MAGIC | Recap | Checklist de qualidade |

# COMMAND ----------

# MAGIC %md
# MAGIC ## Modelo de dados
# MAGIC
# MAGIC O workshop usa **exatamente quatro tabelas**. Todas as tabelas de fatos se ligam a `ativos_geo` por `ativo_id`.
# MAGIC
# MAGIC ```text
# MAGIC ativos_geo (ativo_id)
# MAGIC    ├──< medicoes_horarias (ativo_id)
# MAGIC    ├──< eventos_operacionais (ativo_id)
# MAGIC    └──< rotas_inspecao (ativo_id)
# MAGIC ```
# MAGIC ---
# MAGIC
# MAGIC ### `ativos_geo`
# MAGIC Cadastro de ativos de geração, com capacidade e localização.
# MAGIC
# MAGIC | Coluna | Tipo | Descrição |
# MAGIC |---|---|---|
# MAGIC | `ativo_id` | STRING | Identificador único do ativo (ex.: `ATV-001`). Chave primária. |
# MAGIC | `ativo_nome` | STRING | Nome fictício do ativo (parque ou usina). |
# MAGIC | `tipo_geracao` | STRING | Tecnologia: `Solar`, `Eólica` ou `Hídrica`. |
# MAGIC | `regiao` | STRING | Macroregião: `Norte`, `Nordeste`, `Centro-Oeste`, `Sudeste` ou `Sul`. |
# MAGIC | `estado_nome` | STRING | Nome do estado. |
# MAGIC | `estado_sigla` | STRING | UF do estado (ex.: `SP`, `BA`). |
# MAGIC | `pais` | STRING | País da localidade. |
# MAGIC | `latitude` | DOUBLE | Latitude WGS84 em graus decimais. |
# MAGIC | `longitude` | DOUBLE | Longitude WGS84 em graus decimais. |
# MAGIC | `capacidade_mw` | DOUBLE | Capacidade nominal instalada, em **MW**. |
# MAGIC | `data_comissionamento` | DATE | Data em que o ativo entrou em operação. |
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### `medicoes_horarias`
# MAGIC Medições por ativo e hora: geração, carga e disponibilidade.
# MAGIC
# MAGIC | Coluna | Tipo | Descrição |
# MAGIC |---|---|---|
# MAGIC | `medicao_id` | STRING | Identificador único da medição. |
# MAGIC | `ativo_id` | STRING | Referência ao ativo (`ativos_geo.ativo_id`). |
# MAGIC | `medicao_ts` | TIMESTAMP | Data e hora da medição (granularidade horária). |
# MAGIC | `geracao_mwh` | DOUBLE | Energia gerada na hora, em **MWh**. |
# MAGIC | `carga_mw` | DOUBLE | Carga observada na hora, em **MW**. |
# MAGIC | `disponibilidade_pct` | DOUBLE | Disponibilidade operacional de **0 a 100**. Nunca some este campo; use média. |
# MAGIC | `temperatura_c` | DOUBLE | Temperatura ambiente no ativo, em °C. |
# MAGIC | `qualidade_dado` | STRING | Origem da medição: `Medido` ou `Estimado`. |
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### `eventos_operacionais`
# MAGIC Eventos de manutenção, falha e restrição, com impacto estimado.
# MAGIC
# MAGIC | Coluna | Tipo | Descrição |
# MAGIC |---|---|---|
# MAGIC | `evento_id` | STRING | Identificador único do evento. |
# MAGIC | `ativo_id` | STRING | Referência ao ativo (`ativos_geo.ativo_id`). |
# MAGIC | `inicio_ts` | TIMESTAMP | Início do evento. |
# MAGIC | `fim_ts` | TIMESTAMP | Fim do evento. Duração = `fim_ts - inicio_ts`. |
# MAGIC | `severidade` | STRING | Gravidade: `Baixa`, `Média`, `Alta` ou `Crítica`. |
# MAGIC | `categoria_evento` | STRING | Tipo: `Manutenção planejada`, `Falha de comunicação`, `Proteção acionada`, `Inspeção preventiva` ou `Restrição de rede`. |
# MAGIC | `planejado` | BOOLEAN | `true` se o evento estava no plano de manutenção; `false` se não planejado. |
# MAGIC | `energia_nao_suprida_mwh` | DOUBLE | Estimativa de energia não suprida, em **MWh**. |
# MAGIC | `status_evento` | STRING | Situação: `Aberto` ou `Encerrado`. |
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### `rotas_inspecao`
# MAGIC Pontos ordenados de rotas de inspeção.
# MAGIC
# MAGIC | Coluna | Tipo | Descrição |
# MAGIC |---|---|---|
# MAGIC | `ponto_id` | STRING | Identificador único do ponto na rota. |
# MAGIC | `rota_id` | STRING | Identificador do trajeto. |
# MAGIC | `ordem_ponto` | INTEGER | Sequência crescente dos pontos dentro da rota. |
# MAGIC | `ponto_ts` | TIMESTAMP | Horário em que a equipe passou pelo ponto. |
# MAGIC | `ativo_id` | STRING | Ativo inspecionado (`ativos_geo.ativo_id`). |
# MAGIC | `equipe` | STRING | Equipe responsável: `Equipe Norte`, `Equipe Sul` ou `Equipe Leste`. |
# MAGIC | `latitude` | DOUBLE | Latitude WGS84 do ponto. |
# MAGIC | `longitude` | DOUBLE | Longitude WGS84 do ponto. |
# MAGIC | `distancia_acumulada_km` | DOUBLE | Distância acumulada desde o início da rota, em km. |
# MAGIC | `status_rota` | STRING | Situação do trajeto: `Concluída` ou `Em andamento`. |

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Configuração inicial
# MAGIC
# MAGIC Preencha os widgets com o catálogo, o schema e um prefixo individual. Exemplo de prefixo: `carol`.
# MAGIC
# MAGIC As tabelas serão criadas como `{catalogo}.{schema}.{prefixo}_ativos_geo`.
# MAGIC
# MAGIC >
# MAGIC
# MAGIC <div style="padding: 15px; border-left: 5px solid #d9534f; background-color: #fdf7f7; color: #a94442;">
# MAGIC     <strong>🛑 ATENÇÃO:</strong> Lembre de substituir o caminho do dado pelo caminho da sua pasta. 
# MAGIC     
# MAGIC     Exemplo /Workspace/Users/seu_usuario@seu_email.com/workshop-genie-aibi-energia/dados
# MAGIC
# MAGIC

# COMMAND ----------

dbutils.widgets.removeAll()

# COMMAND ----------

dbutils.widgets.removeAll()
dbutils.widgets.text("nome_catalogo", "workspace", "Catálogo")
dbutils.widgets.text("nome_schema", "workshop_energia", "Schema")
dbutils.widgets.text("seu_prefixo", "prefix_", "Seu prefixo")
dbutils.widgets.text(
    "caminho_dados",
    "/Workspace/Users/{seu_usuario}/workshop-genie-aibi-energia/dados",
    "Caminho da pasta dados",
)

nome_catalogo = dbutils.widgets.get("nome_catalogo").strip()
nome_schema = dbutils.widgets.get("nome_schema").strip()
seu_prefixo = dbutils.widgets.get("seu_prefixo").strip()
caminho_dados = dbutils.widgets.get("caminho_dados").strip().rstrip("/")

assert nome_catalogo, "Informe o catálogo"
assert nome_schema, "Informe o schema"
assert seu_prefixo, "Informe um prefixo individual"
assert caminho_dados, "Informe o caminho da pasta dados"
print(f"Destino: {nome_catalogo}.{nome_schema} | Prefixo: {seu_prefixo}")
print(f"Dados: {caminho_dados}")


# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Módulo 1 — Criar tabelas com SQL
# MAGIC
# MAGIC Execute as células abaixo na ordem. Elas usam os widgets (`${nome_catalogo}`, `${nome_schema}`, `${seu_prefixo}`, `${caminho_dados}`) nas queries.
# MAGIC
# MAGIC Tabelas criadas:
# MAGIC
# MAGIC | CSV | Tabela |
# MAGIC |---|---|
# MAGIC | `ativos_geo.csv` | `{seu_prefixo}_ativos_geo` |
# MAGIC | `medicoes_horarias.csv` | `{seu_prefixo}_medicoes_horarias` |
# MAGIC | `eventos_operacionais.csv` | `{seu_prefixo}_eventos_operacionais` |
# MAGIC | `rotas_inspecao.csv` | `{seu_prefixo}_rotas_inspecao` |
# MAGIC
# MAGIC Se o `read_files` falhar, use a alternativa manual no final deste módulo.
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE `${nome_catalogo}`.`${nome_schema}`.`${seu_prefixo}_ativos_geo` (
# MAGIC   ativo_id STRING COMMENT 'Identificador único do ativo',
# MAGIC   ativo_nome STRING COMMENT 'Nome fictício do ativo (parque ou usina)',
# MAGIC   tipo_geracao STRING COMMENT 'Tecnologia de geração: Solar, Eólica ou Hídrica',
# MAGIC   regiao STRING COMMENT 'Macroregião do ativo',
# MAGIC   estado_nome STRING COMMENT 'Nome do estado',
# MAGIC   estado_sigla STRING COMMENT 'UF do estado',
# MAGIC   pais STRING COMMENT 'País da localidade',
# MAGIC   latitude DOUBLE COMMENT 'Latitude WGS84 em graus decimais',
# MAGIC   longitude DOUBLE COMMENT 'Longitude WGS84 em graus decimais',
# MAGIC   capacidade_mw DOUBLE COMMENT 'Capacidade nominal instalada em MW',
# MAGIC   data_comissionamento DATE COMMENT 'Data em que o ativo entrou em operação'
# MAGIC )
# MAGIC COMMENT 'Cadastro de ativos de geração, com capacidade e localização';
# MAGIC
# MAGIC INSERT OVERWRITE TABLE `${nome_catalogo}`.`${nome_schema}`.`${seu_prefixo}_ativos_geo`
# MAGIC SELECT
# MAGIC   CAST(ativo_id AS STRING) AS ativo_id,
# MAGIC   CAST(ativo_nome AS STRING) AS ativo_nome,
# MAGIC   CAST(tipo_geracao AS STRING) AS tipo_geracao,
# MAGIC   CAST(regiao AS STRING) AS regiao,
# MAGIC   CAST(estado_nome AS STRING) AS estado_nome,
# MAGIC   CAST(estado_sigla AS STRING) AS estado_sigla,
# MAGIC   CAST(pais AS STRING) AS pais,
# MAGIC   CAST(latitude AS DOUBLE) AS latitude,
# MAGIC   CAST(longitude AS DOUBLE) AS longitude,
# MAGIC   CAST(capacidade_mw AS DOUBLE) AS capacidade_mw,
# MAGIC   CAST(data_comissionamento AS DATE) AS data_comissionamento
# MAGIC FROM read_files(
# MAGIC   '${caminho_dados}/ativos_geo.csv',
# MAGIC   format => 'csv',
# MAGIC   header => true,
# MAGIC   inferSchema => true
# MAGIC );
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE `${nome_catalogo}`.`${nome_schema}`.`${seu_prefixo}_medicoes_horarias` (
# MAGIC   medicao_id STRING COMMENT 'Identificador único da medição',
# MAGIC   ativo_id STRING COMMENT 'Referência ao ativo em ativos_geo',
# MAGIC   medicao_ts TIMESTAMP COMMENT 'Data e hora da medição, granularidade horária',
# MAGIC   geracao_mwh DOUBLE COMMENT 'Energia gerada na hora, em MWh',
# MAGIC   carga_mw DOUBLE COMMENT 'Carga observada na hora, em MW',
# MAGIC   disponibilidade_pct DOUBLE COMMENT 'Disponibilidade operacional de 0 a 100. Usar média, nunca soma',
# MAGIC   temperatura_c DOUBLE COMMENT 'Temperatura ambiente no ativo, em Celsius',
# MAGIC   qualidade_dado STRING COMMENT 'Origem da medição: Medido ou Estimado'
# MAGIC )
# MAGIC COMMENT 'Medições por ativo e hora: geração, carga e disponibilidade';
# MAGIC
# MAGIC INSERT OVERWRITE TABLE `${nome_catalogo}`.`${nome_schema}`.`${seu_prefixo}_medicoes_horarias`
# MAGIC SELECT
# MAGIC   CAST(medicao_id AS STRING) AS medicao_id,
# MAGIC   CAST(ativo_id AS STRING) AS ativo_id,
# MAGIC   CAST(medicao_ts AS TIMESTAMP) AS medicao_ts,
# MAGIC   CAST(geracao_mwh AS DOUBLE) AS geracao_mwh,
# MAGIC   CAST(carga_mw AS DOUBLE) AS carga_mw,
# MAGIC   CAST(disponibilidade_pct AS DOUBLE) AS disponibilidade_pct,
# MAGIC   CAST(temperatura_c AS DOUBLE) AS temperatura_c,
# MAGIC   CAST(qualidade_dado AS STRING) AS qualidade_dado
# MAGIC FROM read_files(
# MAGIC   '${caminho_dados}/medicoes_horarias.csv',
# MAGIC   format => 'csv',
# MAGIC   header => true,
# MAGIC   inferSchema => true
# MAGIC );
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE `${nome_catalogo}`.`${nome_schema}`.`${seu_prefixo}_eventos_operacionais` (
# MAGIC   evento_id STRING COMMENT 'Identificador único do evento',
# MAGIC   ativo_id STRING COMMENT 'Referência ao ativo em ativos_geo',
# MAGIC   inicio_ts TIMESTAMP COMMENT 'Início do evento',
# MAGIC   fim_ts TIMESTAMP COMMENT 'Fim do evento. Duração = fim_ts - inicio_ts',
# MAGIC   severidade STRING COMMENT 'Gravidade: Baixa, Média, Alta ou Crítica',
# MAGIC   categoria_evento STRING COMMENT 'Tipo do evento operacional',
# MAGIC   planejado BOOLEAN COMMENT 'true se estava no plano de manutenção',
# MAGIC   energia_nao_suprida_mwh DOUBLE COMMENT 'Estimativa de energia não suprida, em MWh',
# MAGIC   status_evento STRING COMMENT 'Situação: Aberto ou Encerrado'
# MAGIC )
# MAGIC COMMENT 'Eventos de manutenção, falha e restrição, com impacto estimado';
# MAGIC
# MAGIC INSERT OVERWRITE TABLE `${nome_catalogo}`.`${nome_schema}`.`${seu_prefixo}_eventos_operacionais`
# MAGIC SELECT
# MAGIC   CAST(evento_id AS STRING) AS evento_id,
# MAGIC   CAST(ativo_id AS STRING) AS ativo_id,
# MAGIC   CAST(inicio_ts AS TIMESTAMP) AS inicio_ts,
# MAGIC   CAST(fim_ts AS TIMESTAMP) AS fim_ts,
# MAGIC   CAST(severidade AS STRING) AS severidade,
# MAGIC   CAST(categoria_evento AS STRING) AS categoria_evento,
# MAGIC   CAST(planejado AS BOOLEAN) AS planejado,
# MAGIC   CAST(energia_nao_suprida_mwh AS DOUBLE) AS energia_nao_suprida_mwh,
# MAGIC   CAST(status_evento AS STRING) AS status_evento
# MAGIC FROM read_files(
# MAGIC   '${caminho_dados}/eventos_operacionais.csv',
# MAGIC   format => 'csv',
# MAGIC   header => true,
# MAGIC   inferSchema => true
# MAGIC );
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE `${nome_catalogo}`.`${nome_schema}`.`${seu_prefixo}_rotas_inspecao` (
# MAGIC   ponto_id STRING COMMENT 'Identificador único do ponto na rota',
# MAGIC   rota_id STRING COMMENT 'Identificador do trajeto',
# MAGIC   ordem_ponto INT COMMENT 'Sequência crescente dos pontos dentro da rota',
# MAGIC   ponto_ts TIMESTAMP COMMENT 'Horário em que a equipe passou pelo ponto',
# MAGIC   ativo_id STRING COMMENT 'Ativo inspecionado, referência a ativos_geo',
# MAGIC   equipe STRING COMMENT 'Equipe responsável pela inspeção',
# MAGIC   latitude DOUBLE COMMENT 'Latitude WGS84 do ponto',
# MAGIC   longitude DOUBLE COMMENT 'Longitude WGS84 do ponto',
# MAGIC   distancia_acumulada_km DOUBLE COMMENT 'Distância acumulada desde o início da rota, em km',
# MAGIC   status_rota STRING COMMENT 'Situação do trajeto: Concluída ou Em andamento'
# MAGIC )
# MAGIC COMMENT 'Pontos ordenados de rotas de inspeção';
# MAGIC
# MAGIC INSERT OVERWRITE TABLE `${nome_catalogo}`.`${nome_schema}`.`${seu_prefixo}_rotas_inspecao`
# MAGIC SELECT
# MAGIC   CAST(ponto_id AS STRING) AS ponto_id,
# MAGIC   CAST(rota_id AS STRING) AS rota_id,
# MAGIC   CAST(ordem_ponto AS INT) AS ordem_ponto,
# MAGIC   CAST(ponto_ts AS TIMESTAMP) AS ponto_ts,
# MAGIC   CAST(ativo_id AS STRING) AS ativo_id,
# MAGIC   CAST(equipe AS STRING) AS equipe,
# MAGIC   CAST(latitude AS DOUBLE) AS latitude,
# MAGIC   CAST(longitude AS DOUBLE) AS longitude,
# MAGIC   CAST(distancia_acumulada_km AS DOUBLE) AS distancia_acumulada_km,
# MAGIC   CAST(status_rota AS STRING) AS status_rota
# MAGIC FROM read_files(
# MAGIC   '${caminho_dados}/rotas_inspecao.csv',
# MAGIC   format => 'csv',
# MAGIC   header => true,
# MAGIC   inferSchema => true
# MAGIC );
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ### Alternativa — upload manual dos CSVs
# MAGIC
# MAGIC Use este caminho só se o SQL com `read_files` não funcionar.
# MAGIC
# MAGIC 1. Abra **+ New > Add or upload data** ou **Catalog > Create > Create table**.
# MAGIC 2. Faça o download dos CSVs da pasta `dados/` e faça o upload de cada arquivo, um por um.
# MAGIC 3. Revise os tipos detectados, principalmente timestamps, booleanos, latitude e longitude.
# MAGIC 4. Selecione o mesmo catálogo e schema dos widgets.
# MAGIC 5. Crie as tabelas com estes nomes. Não esqueça o **prefixo_**.
# MAGIC
# MAGIC | Arquivo | Nome da tabela |
# MAGIC |---|---|
# MAGIC | `ativos_geo.csv` | `{seu_prefixo}_ativos_geo` |
# MAGIC | `medicoes_horarias.csv` | `{seu_prefixo}_medicoes_horarias` |
# MAGIC | `eventos_operacionais.csv` | `{seu_prefixo}_eventos_operacionais` |
# MAGIC | `rotas_inspecao.csv` | `{seu_prefixo}_rotas_inspecao` |
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Módulo 2 — Genie best practices
# MAGIC
# MAGIC Trate o Genie como uma pessoa analista recém-chegada ao domínio:
# MAGIC
# MAGIC 1. **Comece pequeno:** quatro fontes são suficientes para este objetivo.
# MAGIC 2. **Documente tabelas e colunas:** explicite granularidade e unidades.
# MAGIC 3. **Prefira semântica estruturada:** metric views, expressões SQL e exemplos antes de instruções livres.
# MAGIC 4. **Use exemplos SQL verificados:** ensine joins, períodos e cálculos ambíguos.
# MAGIC 5. **Escreva instruções específicas:** gatilho, dado ausente, ação e pergunta de esclarecimento.
# MAGIC 6. **Evite conflitos:** exemplos e instruções devem usar as mesmas unidades e regras.
# MAGIC 7. **Teste o SQL gerado:** compare com consultas conhecidas antes de compartilhar.
# MAGIC 8. **Itere:** acompanhe feedback e perguntas reais.
# MAGIC
# MAGIC ### Criar o Genie Agent
# MAGIC
# MAGIC 1. Abra **Genie Agents > New**.
# MAGIC 2. Adicione somente as quatro tabelas anteriores.
# MAGIC 3. Depois clique em **CREATE**.
# MAGIC 4. Clique em **Configure** e modifique o nome da sala Genie a Descrição
# MAGIC
# MAGIC > Nome: Seu Nome - Operação de Energia — Workshop
# MAGIC
# MAGIC > Descrição: Assistente para análise da operação de ativos de geração de energia. Permite explorar geração e carga, disponibilidade operacional, capacidade instalada, eventos e energia não suprida, além de rotas de inspeção e distribuição geográfica dos ativos. Responde a comparações por período, estado, região, ativo e tipo de geração, apoiando a identificação de tendências, riscos e oportunidades de melhoria operacional.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Instruções para o Genie Agent (campo *Instructions*)
# MAGIC
# MAGIC O campo de instruções do Genie aceita Markdown. Cole e adapte o bloco abaixo — ele usa títulos, listas e `código` para ficar legível e fácil de manter.
# MAGIC
# MAGIC ````markdown
# MAGIC # Assistente de Operação de Energia
# MAGIC
# MAGIC Você é um analista que responde perguntas sobre uma operação de energia relacionada a eventos, rotas, ativos, disponibilidade e geração de energia.
# MAGIC
# MAGIC ## Regras obritatóras
# MAGIC - Responda em português.
# MAGIC - Sempre cite o período e as unidades.
# MAGIC - Arredonde medidas a duas casas.
# MAGIC - Sempre tente usar gráficos para ajudarem a explicar a métrica.
# MAGIC - Quando tiver dúvida sobre o tipo de agregação, pergunte ao usuário
# MAGIC
# MAGIC ## Regras de negócio
# MAGIC - Disponibilidade: percentual de 0 a 100. Nunca some; use média.
# MAGIC - Geração: em MWh (`geracao_mwh`).
# MAGIC - Capacidade e carga: em MW (`capacidade_mw`, `carga_mw`).
# MAGIC - Energia não suprida: em MWh (`energia_nao_suprida_mwh`).
# MAGIC - Duração de evento: `fim_ts - inicio_ts`.
# MAGIC - Localização: use `estado_nome` e `país`.
# MAGIC - Trajetos: agrupe por `rota_id` e ordene por `ordem_ponto`.
# MAGIC
# MAGIC ## Quando pedir esclarecimento
# MAGIC - "produção" sozinho → pergunte: geração em MWh ou capacidade em MW?
# MAGIC - tendência sem período → pergunte: Qual período deseja analisar?
# MAGIC - "impacto" ambíguo → pergunte: duração do evento ou energia não suprida?
# MAGIC
# MAGIC ````
# MAGIC
# MAGIC > Instruções não substituem bons comentários de coluna, exemplos SQL verificados nem uma camada semântica correta.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Examples na sala Genie
# MAGIC
# MAGIC Na tela do Genie Agent, abra a aba **Examples**. Cada exemplo tem:
# MAGIC
# MAGIC 1. **What question does this query answer?** — a pergunta em linguagem natural
# MAGIC 2. **SQL** — a consulta que responde essa pergunta
# MAGIC 3. **Parameters** — deixe vazio nestes exemplos
# MAGIC 4. **Usage Guidance** — quando o Genie deve reutilizar este padrão
# MAGIC 5. **Preview** para validar, depois **Save**
# MAGIC
# MAGIC <div style="padding: 15px; border-left: 5px solid #d9534f; background-color: #fdf7f7; color: #a94442;">
# MAGIC <strong>🛑 ATENÇÃO:</strong> rode as células Python abaixo. Elas imprimem pergunta, SQL já preenchido e Usage Guidance para copiar. O texto da célula SQL <em>não</em> troca `${widget}` sozinho.
# MAGIC </div>
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC **Exemplo 1** — rode a célula abaixo e copie os três blocos para o Genie.
# MAGIC

# COMMAND ----------

nome_catalogo = dbutils.widgets.get("nome_catalogo").strip()
nome_schema = dbutils.widgets.get("nome_schema").strip()
seu_prefixo = dbutils.widgets.get("seu_prefixo").strip()

pergunta_1 = "Quais estados geraram mais energia e qual a disponibilidade média de cada um?"
guidance_1 = (
    "Use quando a pergunta pedir geração ou disponibilidade por estado. "
    "Sempre faça join com ativos_geo por ativo_id. "
    "Nunca some disponibilidade_pct; use média."
)
sql_exemplo_1 = f"""
SELECT
  a.estado_nome,
  ROUND(SUM(m.geracao_mwh), 2) AS geracao_total_mwh,
  ROUND(AVG(m.disponibilidade_pct), 2) AS disponibilidade_media_pct
FROM `{nome_catalogo}`.`{nome_schema}`.`{seu_prefixo}_medicoes_horarias` m
JOIN `{nome_catalogo}`.`{nome_schema}`.`{seu_prefixo}_ativos_geo` a
  USING (ativo_id)
GROUP BY a.estado_nome
ORDER BY geracao_total_mwh DESC
""".strip()

print("=== What question does this query answer? ===")
print(pergunta_1)
print()
print("=== SQL ===")
print(sql_exemplo_1)
print()
print("=== Usage Guidance ===")
print(guidance_1)

display(spark.sql(sql_exemplo_1))


# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC **Exemplo 2** — rode a célula abaixo e copie os três blocos para o Genie.
# MAGIC

# COMMAND ----------

nome_catalogo = dbutils.widgets.get("nome_catalogo").strip()
nome_schema = dbutils.widgets.get("nome_schema").strip()
seu_prefixo = dbutils.widgets.get("seu_prefixo").strip()

pergunta_2 = "Quais ativos tiveram mais energia não suprida em eventos não planejados?"
guidance_2 = (
    "Use para ranking de impacto operacional. "
    "Filtre planejado = false quando a pergunta for sobre falha ou evento não planejado. "
    "Join com ativos_geo por ativo_id."
)
sql_exemplo_2 = f"""
SELECT
  a.ativo_nome,
  a.estado_nome,
  COUNT(*) AS eventos,
  ROUND(SUM(e.energia_nao_suprida_mwh), 2) AS energia_nao_suprida_mwh
FROM `{nome_catalogo}`.`{nome_schema}`.`{seu_prefixo}_eventos_operacionais` e
JOIN `{nome_catalogo}`.`{nome_schema}`.`{seu_prefixo}_ativos_geo` a
  USING (ativo_id)
WHERE e.planejado = false
GROUP BY a.ativo_nome, a.estado_nome
ORDER BY energia_nao_suprida_mwh DESC
""".strip()

print("=== What question does this query answer? ===")
print(pergunta_2)
print()
print("=== SQL ===")
print(sql_exemplo_2)
print()
print("=== Usage Guidance ===")
print(guidance_2)

display(spark.sql(sql_exemplo_2))


# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Módulo 3 — Laboratório Genie
# MAGIC
# MAGIC Perguntas para fazer no Genie. Inspecione o SQL antes de aceitar a resposta.
# MAGIC
# MAGIC 1. `Quais estados geraram mais energia?`
# MAGIC 2. `Compare a disponibilidade média de Solar, Eólica e Hídrica.`
# MAGIC 3. `Quais eventos críticos tiveram maior duração e energia não suprida?`
# MAGIC 4. `Mostre as rotas concluídas e sua distância final.`
# MAGIC 5. `Como está a produção?`
# MAGIC
# MAGIC Na pergunta 5, o Agent deve pedir esclarecimento.
# MAGIC
# MAGIC Perguntas hipotéticas:
# MAGIC
# MAGIC 6. `Se reduzirmos em 20% a duração média dos eventos críticos, qual seria o impacto estimado na energia não suprida?`
# MAGIC 7. `Se a disponibilidade média de Solar cair 3 pontos percentuais, quais estados sofreriam mais em geração?`
# MAGIC 8. `Se priorizarmos inspeções nos ativos eólicos do Nordeste, quais rotas deveríamos antecipar e por quê?`
# MAGIC 9. `Se encerrarmos todos os eventos abertos nas próximas 24 horas, quanto de energia não suprida deixaria de se acumular com base no histórico?`
# MAGIC 10. `Se concentrarmos a Equipe Leste nas rotas em andamento, qual o impacto operacional estimado?`
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Módulo 4 — AI/BI com Genie Code
# MAGIC
# MAGIC 1. Abra **Dashboards > Create dashboard**.
# MAGIC 2. Abra Genie Code e selecione **Agent mode**.
# MAGIC 3. Referencie as quatro tabelas com `@`.
# MAGIC 4. Rode a célula Python abaixo e copie o prompt já preenchido. Ele já pede os gráficos e os três mapas (choropleth, point e path).
# MAGIC
# MAGIC <div style="padding: 15px; border-left: 5px solid #d9534f; background-color: #fdf7f7; color: #a94442;">
# MAGIC <strong>🛑 ATENÇÃO:</strong> rode a célula para substituir catálogo, schema e prefixo. Sem isso o Genie Code não encontra as tabelas.
# MAGIC </div>
# MAGIC

# COMMAND ----------

nome_catalogo = dbutils.widgets.get("nome_catalogo").strip()
nome_schema = dbutils.widgets.get("nome_schema").strip()
seu_prefixo = dbutils.widgets.get("seu_prefixo").strip()

def tabela(sufixo):
    return f"`{nome_catalogo}`.`{nome_schema}`.`{seu_prefixo}_{sufixo}`"

ativos = tabela("ativos_geo")
medicoes = tabela("medicoes_horarias")
eventos = tabela("eventos_operacionais")
rotas = tabela("rotas_inspecao")

prompt_dashboard = f"""
Crie um dashboard chamado Operação de Energia — Workshop usando as quatro tabelas selecionadas.
Antes de alterar o dashboard, mostre um plano curto.

Crie duas páginas com vários gráficos de tipos diferentes e três mapas na página geográfica.
Evite gráfico de pizza. Títulos em português, unidades nos rótulos e duas casas para percentuais.
Nos gráficos de disponibilidade, comece o eixo Y em 70 (não em 0), para a diferença entre tipos aparecer.

Página 1 — Visão executiva
Coloque uma faixa de KPIs no topo e, abaixo, uma grade de gráficos:
- KPI: geração total em MWh
- KPI: disponibilidade média (%)
- KPI: quantidade de eventos críticos
- KPI: energia não suprida total em MWh
- Gráfico de linha: geração total por dia (some geracao_mwh por data, não por timestamp horário)
- Gráfico de linha: perfil médio de geração por hora do dia (0 a 23), uma série por tipo_geracao — deve aparecer a curva do Solar
- Gráfico de área: geração diária e carga média diária (séries com formas diferentes)
- Gráfico de barras verticais: geração total por tipo de geração (Solar, Eólica, Hídrica)
- Gráfico de barras horizontais: disponibilidade média por tipo de geração (eixo a partir de 70)
- Gráfico combinado: barras de geração e linha de disponibilidade média por estado
- Tabela: eventos críticos com ativo, severidade, duração e energia não suprida

Página 2 — Operação geográfica
Comece pelos mapas, em destaque:
- Choropleth por estado: localidade = estado_nome (State or province), cor = geração total em MWh, tooltip com disponibilidade média. Escala sequencial azul. Título: Geração por estado (MWh). País = Brasil.
- Point map dos ativos: latitude e longitude de ativos_geo, tamanho por capacidade_mw, cor por tipo_geracao, tooltip com ativo, estado e capacidade.
- Path map chamado Rotas de inspeção: ligue latitude e longitude de rotas_inspecao separadamente para cada rota_id, respeitando ordem_ponto. Uma cor por equipe. Tooltip com rota, ativo, horário, distância e status.

Em seguida, os demais gráficos:
- Gráfico de barras: geração total por estado
- Gráfico de barras agrupadas (não 100% empilhado): quantidade de eventos por severidade em cada estado
- Gráfico de dispersão: capacidade_mw no eixo X e geração total no eixo Y, um ponto por ativo, cor por tipo_geracao
- Heatmap: disponibilidade média por estado e tipo de geração
- Gráfico de barras: distância final das rotas por equipe (máximo de distancia_acumulada_km por rota, depois média ou soma por equipe)
- Gráfico de linha: distancia_acumulada_km ao longo de ordem_ponto, uma série por equipe (não por rota_id)
- Tabela: ranking de ativos com estado, tipo, geração, disponibilidade e energia não suprida

Regras dos mapas:
- rota_id separa os trajetos
- ordem_ponto define a sequência
- não inverter latitude e longitude
- filtros não podem eliminar pontos intermediários da rota (isso quebra o path)

Adicione filtros globais de estado e tipo de geração.

Use as tabelas do catálogo {nome_catalogo} e do schema {nome_schema} com prefixo {seu_prefixo}_ :
- {ativos}
- {medicoes}
- {eventos}
- {rotas}
""".strip()

print(prompt_dashboard)


# COMMAND ----------

# MAGIC %md
# MAGIC ### Usando uma imagem de referência para estilizar
# MAGIC 1. Tire print de algum website
# MAGIC 2. Copie e cole a imagem no chat da Genie e peça:
# MAGIC  > Estilize o dashboard seguindo como referência cores da imagem em anexo.

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Módulo 5 — Vega-Lite Custom Visualization (opcional)
# MAGIC
# MAGIC 1. Abra o dashboard do Módulo 4.
# MAGIC 2. Abra o Genie Code em **Agent mode**.
# MAGIC 4. Selecione o gráfico **Distância acumulada por equipe**
# MAGIC 3. Rode a célula abaixo e copie o prompt.
# MAGIC
# MAGIC <div style="padding: 15px; border-left: 5px solid #d9534f; background-color: #fdf7f7; color: #a94442;">
# MAGIC <strong>🛑 ATENÇÃO:</strong> rode a célula antes de copiar.
# MAGIC </div>
# MAGIC

# COMMAND ----------

prompt_vega = (
    "Transforme esse gráfico em um de gráfico feito com custom visualization" 
)

print(prompt_vega)


# COMMAND ----------

# MAGIC %md
# MAGIC Depois que o Genie Code concluir, confira se o widget é uma **Custom Visualization**.
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC ## Módulo 6 — Importar BI com Genie Code (opcional)
# MAGIC
# MAGIC 1. Crie ou abra um dashboard vazio.
# MAGIC 2. Abra Genie Code, inicie uma conversa e escolha **Import from a BI tool** ou digite `/importBI`.
# MAGIC 3. Anexe `.pbit`, `.twb`, `.twbx`, `.tds` ou `.tdsx`; para arquivos grandes, use um caminho em Volume.
# MAGIC 4. Forneça também uma captura de tela de boa qualidade.
# MAGIC 5. Mantenha a aba aberta enquanto o agente trabalha.
# MAGIC 6. Revise datasets, relacionamentos, cálculos, filtros, números e layout.
# MAGIC 7. Promova metric views locais finalizadas para o Unity Catalog.
# MAGIC
# MAGIC Exemplo com Volume:
# MAGIC
# MAGIC ```text
# MAGIC /importBI
# MAGIC @/Volumes/meu_catalogo/meu_schema/meu_volume/modelo_energia.pbit
# MAGIC ```