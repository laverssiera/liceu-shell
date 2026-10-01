#!/usr/bin/env bash
# Check pos-fato para push em main (issue #13).
#
# A protecao de branch (PR obrigatorio + CI verde) e indisponivel no plano
# Free para repositorio privado. Este check nao impede o push — ja aconteceu —
# mas FALHA o workflow e abre uma issue quando o commit que chegou em main nao
# e o merge de um pull request. Assim um push direto nunca passa em silencio:
# fica registrado quem, o que e quando, e a CI de main fica vermelha ate
# alguem responder.
#
# Criterio: o commit HEAD do push tem de estar associado a um PR MERGEADO em
# main cujo merge_commit_sha e o proprio HEAD. Cobre squash, merge commit e
# rebase-merge (no rebase, merge_commit_sha e o ultimo commit reaplicado).
# Um push direto de N commits falha pelo HEAD; os N sao listados na issue.
#
# Entradas (env): GH_TOKEN, REPO, SHA, BEFORE, PUSHER. DRY_RUN=1 nao abre issue
# (para simular localmente contra commits ja em main).
#
# COMO LER O VERMELHO DESTE CHECK — e o que ele NAO significa.
#
# A execucao que acusa um push direto fica vermelha PARA SEMPRE. O GitHub nao
# reexecuta workflow passado, e fechar a issue nao muda a conclusao da
# execucao. O painel limpa quando o PROXIMO push em main vier de um PR
# mergeado: essa execucao nova passa a ser a mais recente deste workflow.
#
# Entao 'Main Guard vermelho em main' NAO quer dizer que a guarda esta
# quebrada, nem que o push segue sem resposta. Quer dizer que houve um push
# direto EM ALGUM MOMENTO. Para saber se ainda importa, duas coisas:
#
#   a DATA da execucao vermelha — ela e do dia do push, nao de hoje
#   a ISSUE que ela abriu — se esta fechada, o push foi respondido
#
# Isto esta escrito aqui porque a leitura errada JA ACONTECEU: em 2026-09-29
# este vermelho foi relatado como 'gate permanentemente vermelho', o que
# sugeria defeito na guarda. Nao era: era um alarme pos-fato de 19/09, com a
# issue #1 aberta e fechada, esperando o proximo merge por PR. Um alarme que
# e lido como defeito perde a funcao de alarme.
set -euo pipefail

short="${SHA:0:7}"
merged_prs=$(gh api "repos/$REPO/commits/$SHA/pulls" \
  --jq "[.[] | select(.merged_at != null and .base.ref == \"main\" and .merge_commit_sha == \"$SHA\") | .number]")

if [ "$merged_prs" != "[]" ]; then
  echo "OK: $short e o merge do PR $merged_prs em main."
  exit 0
fi

echo "::error::push direto em main: $short nao e o merge de nenhum pull request."

# Commits que este push trouxe (BEFORE pode ser 0000... se main nasceu agora).
if [[ "$BEFORE" =~ ^0+$ ]]; then
  commits="- $short (primeiro push de main)"
else
  commits=$(gh api "repos/$REPO/compare/$BEFORE...$SHA" \
    --jq '.commits[] | "- `\(.sha[0:7])` \(.commit.author.name) — \(.commit.message | split("\n")[0])"' \
    || echo "- (compare indisponivel: $BEFORE...$SHA)")
fi

# Uma issue por push (dedupe pelo SHA curto no titulo).
title="Push direto em main sem PR: $short"
existing=$(gh issue list --repo "$REPO" --state all --search "in:title \"$short\"" --json number --jq '.[0].number // empty')
if [ -n "$existing" ]; then
  echo "issue #$existing ja registra este push."
  exit 1
fi

body=$(cat <<BODY
**\`$short\` chegou em \`main\` sem passar por pull request.** Push de @$PUSHER.

Commits deste push:
$commits

Nenhum deles esta associado a um PR mergeado em \`main\`. A CI de \`main\` rodou depois do fato — se falhou, o codigo ja esta em \`main\`; se passou, passou sem revisao.

Por que isto existe: a protecao de branch e indisponivel no plano atual (ARCHIMEDES #13). Este check nao impede o push; garante que ele nao passa em silencio.

O que fazer:
1. Se foi engano: abrir um PR retroativo com o diff (\`git diff $BEFORE $SHA\`) para revisao, ou reverter e reabrir como PR.
2. Se foi deliberado: registrar aqui o motivo e fechar.

Gerado por \`.github/workflows/main-guard.yml\`.
BODY
)

if [ "${DRY_RUN:-}" = "1" ]; then
  printf 'DRY_RUN: abriria a issue "%s":
%s
' "$title" "$body"
  exit 1
fi
# A label e conveniencia; a issue e o registro. Sem label no repo, abre sem ela.
label_args=()
if gh label list --repo "$REPO" --json name --jq '.[].name' | grep -qx "ci-cd"; then
  label_args=(--label "ci-cd")
fi
gh issue create --repo "$REPO" --title "$title" "${label_args[@]}" --body "$body"
exit 1
