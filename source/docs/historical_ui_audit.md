# Auditoria transversal da UI histórica — FFBE Global

Data: 2026-11-08
Classificação: diagnóstico. **Nenhuma edição funcional nesta rodada.**
Escopo: preview Global junho/julho 2016; branch feature/historical-progression.
Estado: **NÃO AUDITADO COMO FIEL À UI DE 2016**. A build 9066 corrige só dois sintomas.

## Critério de aceitação

A progressão deve controlar duas dimensões: (1) disponibilidades reais de botões,
telas, sistemas, abas, missões, prêmios e ações; (2) aparência, navegação,
hierarquia e nomenclatura da interface da época. Ocultar eventos não é suficiente.
Nenhum botão oculto pode continuar operável por touch nativo, rota secundária
ou requisição direta ao servidor. Desbloqueios de história/nível permanecem.

## Fontes contemporâneas e limites

- Square Enix, lançamento de 30/06/2016: combate, exploração, quests diárias,
  achievements, leaderboards e summons já disponíveis:
  https://www.prnewswire.com/news-releases/full-scale-final-fantasy-game-now-available-for-mobile-devices-300292508.html
- Capturas Android adicionadas em julho de 2016 (referência de HOME, abas,
  nomes e telas): https://www.mobygames.com/game/79645/final-fantasy-brave-exvius/screenshots/
- Anúncios históricos Global: Arena introduzida em 10/11/2016, quando
  Colosseum foi movido para dentro de Arena; Expeditions em 19/06/2017;
  6★ em 30/09/2016:
  https://exvius.fandom.com/wiki/News/Archives/2016_-_2021
- Versão 2.0 (23/02/2017) reformou Home, quests e summons:
  https://www.player.one/final-fantasy-brave-exvius-version-20-launches-new-story-esper-and-more-585839

O master Global 9.0.0 registra o estado final, não o calendário de 2016.
Datas exatas de estreia de Panel Quest, Equipment Enhancement e outros
sistemas ainda precisam de fontes primárias. "Rookie Panel Quests Revamp"
de novembro de 2021 não prova que o sistema começou naquele ano.

## Inventário de risco por superfície

| Superfície | Evidência no código | Problema | Ação |
|---|---|---|---|
| Home | source/exvius/home_carousel.js; Arena, World, Expedition, Craft, Espers, Vortex, Equipment Enhancement | Cards e touches próprios, sem consulta a historical_month; UI pode ser anacrônica | Gate por mês em render e touch, + reconstrução da organização de 2016 |
| Arena/Colosseum | home_carousel.js usa rótulo Arena e isOpenedArena | Arena não existia no lançamento, Colosseum sim | Antes 10/11/2016 oferecer Colosseum, depois Arena; não ocultar os dois |
| Expeditions | home_carousel.js cria sgExpdConnectScene diretamente | Chegou 19/06/2017, pode contornar F_FUNCTION_MST | Esconder visual e bloquear ação/rota até estreia |
| Equipment Enhancement | home_carousel.js desenha comando separado | Conteúdo posterior sem data/habilitação verificada | Determinar data, ocultar UI e negar rota antes dela |
| Quests | ffbe_player.py serve daily, panel, SP challenge | Quests diárias existiam no lançamento; variantes tardias não | Matriz de famílias com datas, tabs e prêmios distintos |
| Vortex | event_archive.py / serve_event_gate / summon_menu.js | Índice preservado com 757 áreas, sem estreias de 2016 auditadas; chambers nativas entram por caminhos adicionais | Auditar early chambers, trials, tabs, missões e datas; não confundir 0 eventos auditados com 0 eventos históricos |
| Summon | historical_summons.py e ffbe_gacha.py | Filtro parcial de pools, não de todas as ofertas, ganhos e abas | Same policy em UI, action, transaction, garantias e todos os grants |
| Units/Espers | player_state.py / ffbe_player.py | Evoluções, raridades, materiais e sistemas posteriores potencialmente disponíveis | Gating de ações e árvores por data + progresso |
| World/Story | mapa e F_FUNCTION_MST final; navegação nativa | Regiões, story chapters e espers futuros podem aparecer | Time gate em mapa e roteiros, preservando progressão |
| Craft/Shop | home_carousel.js, serve_lapis_shop e shop_archive | Receitas, pacotes, moedas e trocas da era final | Filtrar UI, preço e autorização antes de comprar/receber |
| Mail/Login | ffbe_config.py LOGIN_MONTH padrão 2021-Jun; ANNIVERSARY_TICKET=1 | Recompensas do futuro podem entrar no save de 2016 | Data de referência deve vir do save, sem fallback 2021 |
| Economy | seasons.json default_login_bonus com 2000 Lapis, 100000 Gil e 500 FP | Valores criados para catch-up, não lançamento comprovado | Reconstruir baseline histórico, não atribuir sem evidência |
| Season UI | ffbe_state.py SEASON_SELECTOR + seasons.json default off | Seletor do servidor é global ao processo; não segue meta.historical_month | Estado único por save para todos os consumidores |
| Client menu | title_menu.js e android_test.js | Flag JS do save nasce do bridge de título; pode falhar ou não ser atualizada em uma UI já aberta | Estado runtime falha fechado, invalidate caches após mudança |

## Mecanismos existentes a reutilizar antes de criar qualquer helper

1. Native F_FUNCTION_MST tem 22 chaves, incluindo FUNCTION_PANEL_QUEST,
   FUNCTION_COMEBACK_QUEST, FUNCTION_EMBLEM_EVENT, FUNCTION_REEL_EXPEDITION,
   FUNCTION_REEL_COLOSSEUM, FUNCTION_REEL_DIMENSION, FUNCTION_REEL_WORLD,
   FUNCTION_SP_CLASSUP, FUNCTION_WORLD_CHANGE e FUNCTION_REEL_BEAST. O valor
   de 2024 não representa disponibilidade de 2016. Nem todos os modos da
   Home passam por esse mecanismo.
2. O sistema de season do upstream serve campanhas e badges; o seu campo
   home_icons está documentado como ainda não dirigido pelo servidor.
   Não é equivalente ao marcador de mês do PlayerState.
3. LocalGame inicializa GACHA_ONLY=all, GACHA_CAMPAIGN=all,
   GACHA_CATALOGUE=1 e EXVIUS_EVENT_ARCHIVE=1. Filtros parciais sobre
   essas coleções são insuficientes para garantir fidelidade.
4. O servidor pode conceder itens sem gacha (mail, tutorial, missão, loja,
   login, evolução). Proibição na UI **não é** controle de entitlement.

## Proposta arquitetural (nenhum código implementado)

- Inventariar cada superfície e feature_id: primeiro mês Global documentado,
  fontes, condições de story/rank, requisitos de cena e status de confiança.
- Expor uma decisão única por save, com estados: available / locked /
  not-introduced / unverified; recusar por padrão conteúdo sem fonte.
- Consumir a decisão nos mecanismos existentes de FunctionMstList, Home,
  menus, abas, listas, gate de ação e grants do servidor. Evitar novos
  overrides locais duplicados.
- Distinguir equivalência de **funcionalidades históricas** da fidelidade
  **visual** do layout; comparar capturas de 2016 sem presumir que assets
  do cliente Global 9.0 reproduzem seu visual original.
- Aplicar refresh/invalidação de UI após avançar o mês, com save monotônico.

## Bloqueios e testes antes do próximo APK

- Matriz de render + toque + request + recompensa por mês:
  2016-06, 2016-07, 2016-09, 2016-11 e 2017-06.
- Cenários concretos: Colosseum sem Arena em junho; Arena em novembro;
  Expedition ausente em 2016 e liberável em junho/2017;
  Panel Quest diferente de daily quest; nenhuma recompensa 2021/2024.
- Snapshot visual da Home, menu, world, units, summons, shops, quests e
  Vortex contra screenshots contemporâneas.
- Testes de backend: recurso indisponível não credita nem consome moeda,
  nem deixa unlock de campanha/quest futura.
- Verificar no Android o hook nativo; testes Python ou assinatura não
  demonstram que o botão sumiu efetivamente.
- Atualização incremental com mesmo pacote/certificado, versionCode maior,
  preservando dados do usuário e o índice installed.json.

**Decisão:** bloquear nova rodada de patches isolados de UI até fechar
a matriz por feature e definir a integração central. O APK 9066 é prova
de runtime básico, não prova de fidelidade histórica.
