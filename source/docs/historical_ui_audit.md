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

## Implementação inicial da política (iteraçao 1)

O mapa inicial foi incorporado ao módulo preexistente
`source/server/historical_progression.py`: `FEATURE_INTRODUCED`,
`historical_features` e `feature_available`. Entradas sem data provada
recebem `None` e são recusadas na prévia; saves sem histórico seguem
intocados. O `offline_menu.status` envia a mesma projeção à interface,
que consome os indicadores em `title_menu.js`, `home_carousel.js` e
`android_test.js`, sem recalcular datas no JavaScript.

Cobertura inicial: Expedition (UI, recurso nativo, transações), Panel Quest
(recurso nativo, tela e requests de claim), botão de Equipment Enhancement
na Home, calendário de login 2021, 8º aniversário, catch-up e SP Challenge.
É bloqueio conservador da **prévia**, não supressão de funcionalidades
historicamente comprovadas do jogo original. Datas de sistemas futuros ainda
não auditados não são "estimadas" com base no catálogo final.

**Pendente antes de entregar uma nova build:** recuperar o Colosseum original
como modo da Home no lançamento, ajustar Arena de 2016-11, auditar as quests
diárias originais e o resto das recompensas/loja, e validar a aparência no
Android. A política não torna toda a UI fiel nem torna todas as rotas seguras.

## Transição Colosseum / Arena — navegação reconstruída (iteraçao 2)

As capturas Android de julho/2016 e o comunicado Global de novembro/2016
confirmam Colosseum como a entrada original da Home; Arena substituiu seu
nome/rota quando estreou, mantendo Colosseum acessível internamente.
O acesso original ao Colosseum continua condicionado a alcançar Grandshelt.

A inspeção do binário *exato* embutido no APK 0.1.24 localizou
`GameSceneFactory::createGameScene`: a tabela nativa aponta
`sceneId=11000` para `ClsmVsCpuEntryScene` e `11001` para
`ClsmVsCpuMyPageScene`. `ClsmVsCpuEntryScene::backScene` retorna ao
identificador nativo 100 (Home). Nenhuma classe/tela paralela foi criada.

`home_carousel.js` agora reutiliza o artwork antigo
`mypage_colosseum`, o estado de desbloqueio da história e o
`changeSceneWithSceneID(11000)` já importado para abrir Colosseum
antes de Arena. No mês de estreia de Arena (2016-11), a Home mantém
a transição nativa moderna. O mesmo marcador mensal determina a
autorização no `exvius_actions.py`: sete requests `Rb*` são recusados
antes de custos/prêmios em períodos antigos; os quatro requests
`Clsm*` não são bloqueados por essa regra.

`build_historical_preview_apk.py` foi atualizado para incluir o bytecode
de `exvius_actions.py` na próxima build. Testes da projeção da Home,
requisições aceitas/recusadas e manifest do pacote foram adicionados.

**Ainda pendente:** confirmação da abertura e do retorno no Android real,
da renderização do rótulo da Home e da manutenção das orbs/ranks de 2016.
A prévia instalada 9066 **não** contém essa correção. Não reemitir
o APK até a validação geral da UI e da compatibilidade incremental.

### Verificações adicionais do Colosseum

Foi encontrado mais um problema no APK 9066: `exvius_colosseum.py`
abria `colosseum_encounters.json` por `Path(__file__)`, incompatível
com o bytecode carregado de `app.imy`. A implementação agora reutiliza
`pkgutil.get_data`, como o carregador já existente do Vortex.
O arquivo está presente no APK-base e na prévia 9066; o teste de
`zipimport` com Python 3.10 carregou **75 grupos de encontros**.
`exvius_colosseum.pyc` também entra no empacotador da próxima prévia.

A suíte upstream `test_actions_arena.py` não pôde executar no notebook:
o fixture de `PlayerState.load` depende de tabelas em
`mst_decoded/` na raiz, ausentes no checkout atual. Os casos específicos
com o dispatcher simulado passaram, mas não substituem os testes
completos da economia, dos rounds e das batalhas do Colosseum.

**Ainda não autenticados para 2016:** capacidade e regeneração de orbs
(3 antes da Arena, 5 a partir do lançamento de Arena), ranks de
Colosseum e a equivalência exata entre a navegação visual de 2016
e a tela nativa final. Antes de afirmar fidelidade, validar em aparelho
real; não alterar os dados do usuário nem forçar reinstalação.

## Colosseum: orbs, dificuldades e prêmios (iteraçao 3)

### Evidência Global de 2016

- [Anúncio Global da Arena, 10/11/2016](https://exvius.fandom.com/wiki/News/Archives/2016_-_2021):
  quando Arena substituiu a entrada Colosseum, a capacidade compartilhada
  aumentou de **3 para 5 orbs**. Os orbs recuperam **1 por hora**
  (corroborado também pela [documentação Colosseum](https://exvius.fandom.com/wiki/Colosseum)).
- [Relato Global em 09/07/2016](https://www.neogaf.com/threads/final-fantasy-brave-exvius-ot-classic-sprite-based-jrpg-goodness-up-global-launch.1219944/page-89):
  jogador já havia completado **Intermediate S-5**. Essa é a
  *primeira evidência contemporânea encontrada*, **não** a data comprovada
  de implantação do Intermediate. Na prévia junho segue bloqueado por cautela,
  julho habilita depois da conclusão de Beginner.
- [Anúncio Global da dificuldade ADV, 29/09/2016](https://exvius.fandom.com/wiki/News/Archives/2016_-_2021):
  Advanced passa a existir em setembro; não pode ser desbloqueada em junho/julho.

### Auditado contra os masters originais do cliente final

Lidas por HTTP Range com verificação CRC (sem baixar o pacote de 1,2 GB):
`data/mst_decoded/F_CLSM_PROGRESS_MST.ndjson` e
`data/mst_decoded/F_CLSM_ROUND_MST.ndjson` do pacote original
`data-001` referenciado em `data/latest.json`. São arquivos
**ignorados pelo Git**, não incluídos no commit.

- 75 rounds no total: 25 Beginner (grade 1), 25 Intermediate (grade 2),
  25 Advanced (grade 3); cada grade tem D/C/B/A/S, 5 rounds por rank.
- Transições: `10505 -> 20101` (Beginner -> Intermediate) e
  `20505 -> 30101` (Intermediate -> Advanced).
- Primeiro round `10101`: uma orb por batalha, chefe após 1.000 pontos,
  recompensa inédita `50:1:100` (100 Lapis) e recompensa repetível
  `20:101000100:1:100` (item comum).
- Todos os 75 registros têm as duas recompensas e um master de progressão.
  Os tipos variam (item 20, equipamento 21, materia 22, Lapis 50,
  receita 60). O servidor já valida se cada prêmio pode ser projetado no
  inventário; prêmio desconhecido recusa a transação com rollback.

### Implementação

`historical_progression.historical_colosseum_orb_cap` estabelece 3 orbs
entre junho e outubro/2016, 5 de novembro/2016 em diante (até que haja fonte
para outra mudança); saves não históricos retêm capacidade 10 do upstream.
A capacidade é derivada pelo `PlayerState.orb_capacity` e consumida pelo
`orb_view`, gasto, recarga por Lapis e reposição ao subir rank — sem criar
um segundo saldo nem alterar os outros três tipos de orb.

`exvius_colosseum._run` recusa acesso direto a grades não lançadas, antes
do gasto. Um boss vencido não desbloqueia uma grade futura antecipadamente.
Ao avançar o mês, `entry` libera a próxima grade se o último chefe
anterior já havia sido vencido; isso não reexecuta o prêmio nem consome
outra orb. Saves comuns mantêm sua navegação padrão.

### Pendências

- Confirmar a data **exata** em que Intermediate entrou no Global. Julho é
  um marco documental conservador, sujeito a correção.
- Identificar o anúncio posterior que elevou a capacidade de 5 para 10.
  Não antecipar 10 enquanto não houver uma data Global comprovada.
- Validar renderização das três orbs e os botões de ranks no Android
  físico. A suíte completa `test_actions_arena.py` requer outras tabelas
  mestres, não disponíveis no checkout atual. Os testes isolados de
  débito, recuperação, crédito e rollback já não dependem delas.
- Esta implementação ainda NÃO está no APK instalado 9066.
