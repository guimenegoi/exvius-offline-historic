# FFBE — arquivo histórico de investigação

**Projeto descontinuado em 10 de novembro de 2026.**

Esta é uma coleção pequena de **resultados de pesquisa técnica e histórica**
sobre *Final Fantasy Brave Exvius* Global e sobre tentativas anteriores
de preservação offline. **Não é um jogo, servidor, fork funcional ou
projeto em desenvolvimento.** Não há APK, código de jogo, imagens,
bibliotecas, hooks, builds, nem instruções de instalação.

## O que foi preservado

| Área | Material |
| --- | --- |
| Datas e fontes Global 2016–2024 | [Cronologia](research/chronology/CRONOLOGIA_GLOBAL_2016_2024.md) e [limites de validação](research/chronology/VALIDATION_LIMITS.md) |
| Catálogos investigados | [2016](research/chronology/catalogue_2016.json), [auditoria 2016](research/chronology/audit_2016.json), [candidatos 2017–2024](research/chronology/candidates_2017_2024.json) |
| Incompatibilidade de motores | [Conclusões de portabilidade](research/architecture/FINAL_CONCLUSIONS.md), [estudo v0.1.30](research/architecture/PORTABILIDADE_V0130.md), [fronteira JNI](research/architecture/JNI_BOUNDARY.md) |
| Protocolo do cliente Global 9.0.0 | [Pesquisa de endpoints e contratos](research/protocol/README.md) |
| Mapeamentos de ações | [Relatórios e limites](research/request-analysis/README.md) |
| Preview histórico 9088 | [Auditorias e resultados anteriores](research/preview-9088/README.md) |

## Interpretação e limites

- **Confirmado**, **inferido** e **não homologado** são categorias
  diferentes. Datas JP, reprises GL e dados do catálogo Offline
  **não substituem** a estreia original Global ou os IDs de mestre.
- Os relatórios estáticos de payloads não provam funcionamento real
  do servidor. As experiências 9088 não provam compatibilidade
  com o runtime JNI da versão 0.1.30.
- Arquivos `*.json` deste repositório são índices e resultados
  de pesquisa, **não dados oficiais do jogo, tabelas de produção ou
  especificação de execução autorizada**.
- Algumas notas históricas apontam para arquivos/scripts removidos
  do HEAD. São referências de proveniência, não uma dependência
  operacional a restaurar.

## Proveniência do arquivo

Este repositório anteriormente era um fork de
[Elvlin/exvius-offline](https://github.com/Elvlin/exvius-offline).
As conclusões de pesquisa foram selecionadas de:

- commit **`b045eef`**: investigação Global, catálogo e
  fronteira da versão 0.1.30;
- commit **`367265e`**: auditorias do protótipo histórico 9088;
- documentos anteriores de protocolo no `source/docs/`.

O histórico Git antigo permanece acessível para auditoria e recuperação,
mas **não representa uma branch de desenvolvimento nem um produto
mantido**. Nenhuma atualização do upstream será integrada.

## Direitos

*Final Fantasy Brave Exvius*, personagens e demais ativos pertencem
a Square Enix, gumi e seus respectivos titulares. Arquivo de notas
não oficial e sem vínculo com as empresas. Não redistribui ativos de jogo.
