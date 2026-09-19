# LICEU 6.0 — Universal Shell

Implementação de referência do L6-FE-001: shell, drawers (evidência, autoridade,
lineage) e o **JOHN Context Panel** (§8). Estático — um `index.html`, sem build.

Até 2026-09-19 isto existia só como dois artefatos no claude.ai. Aqui vira repositório,
consumindo [`@liceu/design-tokens`](https://github.com/laverssiera/liceu-design-tokens)
**por tag**: nenhum token é definido neste repositório.

## O que a tela mostra

O que existe, não o que está previsto. Onde não há dado, ela diz que não há (R02).
Hoje a cadeia causal está em 0/5: todos os campos são travessão, a época é "não
estabelecida", o dourado não acende (R04), e o painel do JOHN explica por quê — nomeando
os três eventos que levam o nome do JOHN e que ele não emite.

## O JOHN Context Panel — a condição

Persistente, à direita. **Nunca tem botão que execute ou autorize.**

| Ação | Natureza |
|---|---|
| Explicar, Simular, Comparar, Evidência | leitura (`data-read`) |
| Escalar → Mãe | transfere para quem decide — não decide (`data-transfer`) |

Se o painel tivesse um botão que parecesse autorização, violaria a R01 e o P03 ao mesmo
tempo, no componente mais visível do produto. Por isso a condição é **teste**, não prosa:
`scripts/check.py` falha se qualquer botão do painel carregar verbo de autoridade ou
execução (autorizar, aprovar, executar, decidir, promover, assinar, confirmar — e os
equivalentes em inglês). Na primeira execução ele pegou o próprio rótulo original de
Escalar ("quem decide · não decide"); o rótulo mudou, o check não.

## O que a CI aplica

```bash
python scripts/check.py
```

1. Tokens consumidos por tag (`liceu-design-tokens@vX.Y.Z`), nenhum `--liceu-*` definido aqui.
2. Painel do JOHN: exatamente 4 ações de leitura + 1 de transferência; zero verbos de autoridade.
3. Todo campo sem `data-value` é `—` (ou `0` literal) em `.none` — nunca exemplo, nunca id inventado.
4. `authority_epoch` só mostra número com `data-established="true"`.
5. Barra de proveniência presente com os cinco campos.

## Quando houver dado (D2)

Nenhum componente muda de estrutura. O shell passa a ler do boundary do CORE; cada campo
troca o travessão pelo valor com `data-value`; a barra de proveniência passa de vermelha a
preenchida por campo; a época mostra número quando o CORE disser que há época vigente.
Se algum componente precisar mudar de estrutura para isso, o desenho estava errado.
