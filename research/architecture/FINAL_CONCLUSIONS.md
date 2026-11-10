# Conclusões de portabilidade e inviabilidade do protótipo

**Resultado final, não plano de implementação.**

1. O preview histórico 9088 foi produzido sobre o runtime antigo
   (Offline 0.1.24, código de versão 9064), com Python 3.10 / Chaquopy
   e camadas experimentais. Os testes de interface da época **não
   comprovam** fidelidade à UI Global de junho de 2016.
2. O APK oficial Offline 0.1.30 (versionCode 9070) tinha SHA-256
   `98875e7b8ebcd04794b36392f8afa71c207bebeba2f90d939ee9572f034e95e2`
   e passou a delegar regras de jogo a JNI/C++.
3. O código público do tag 0.1.30 **não oferecia a implementação
   correspondente** de `NativeRules`/regras JNI publicada no binário.
   Enxertar o código Python anterior não bloquearia invocações
   diretas de eventos, summons ou concessões de recompensas.
4. A análise de `classes7.dex` identificou caminhos de
   `DirectRules.respond()` e `DirectFiles.materializeFile()`
   para `NativeRules.localRequest()`. Interceptar apenas a primeira
   rota seria incompleto.
5. Não houve integração ABI/serialização comprovada, APK histórico
   v0.1.30 funcional, validação de save nem teste Android de todos os
   caminhos de concessão e cobrança. **Não alegar que existiu**.
6. O estudo concluiu que intervenções visuais sem gate transacional
   poderiam aparentar fidelidade enquanto permitiam conteúdo posterior.
   Esse foi um fator para descontinuar o experimento.

Arquivos de origem:
- [PORTABILIDADE_V0130.md](PORTABILIDADE_V0130.md)
- [JNI_BOUNDARY.md](JNI_BOUNDARY.md)
- [Auditoria de preview](../preview-9088/historical_ui_audit.md)

Não manter builds, APKs, engine, hooks, FRIDA, scripts de execução ou
plano de retomada neste arquivo. A autoria/estado de quaisquer
dependências externas deve ser reavaliada caso haja estudo futuro.
