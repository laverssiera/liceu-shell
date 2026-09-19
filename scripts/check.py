#!/usr/bin/env python3
"""Verificacoes do Universal Shell (L6-FE-001) — o que a CI aplica.

1. TOKENS CONSUMIDOS, NUNCA COPIADOS: nenhum ``--liceu-*`` e DEFINIDO no
   HTML; a folha vem de liceu-design-tokens por TAG (jsDelivr, @vX.Y.Z).
2. R01 / P03 no JOHN Context Panel: nenhum botao do painel executa ou
   autoriza. Explicar, Simular, Comparar e Evidencia sao leitura
   (``data-read``); Escalar transfere (``data-transfer``) — e so isso.
   Qualquer botao cujo rotulo contenha verbo de autoridade ou execucao
   falha o check.
3. R02 / R05: todo ``<dd>`` sem ``data-value`` no painel e nos drawers e
   travessao ("—") ou zero literal — nunca exemplo, nunca id inventado.
4. R04: o chip de authority_epoch so mostra numero se ``data-established="true"``.
5. R07: a barra de proveniencia existe e tem os cinco campos.

Sem dependencias (html.parser da stdlib).
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"

# Verbos que NUNCA aparecem num botao do painel do JOHN. O painel le e
# transfere; autorizar, executar, decidir, aprovar e promover sao atos de
# outras camadas (Mae, OPERA) e de outro componente (gaveta de autoridade).
FORBIDDEN_VERBS = re.compile(
    r"\b(autoriz\w*|aprov\w*|execut\w*|decid\w*|promov\w*|assin\w*|confirm\w*|"
    r"authoriz\w*|approv\w*|execute\w*|decide\w*|promote\w*|sign\w*|confirm\w*)\b",
    re.IGNORECASE,
)
ALLOWED_READ = {"explain", "simulate", "compare", "evidence"}
ALLOWED_TRANSFER = {"authority"}
PROV_FIELDS = ["contexto", "evidência", "autoridade", "lineage", "ciclo"]


class Shell(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: list[tuple[str, dict]] = []
        self.token_links: list[dict] = []
        self.panel_buttons: list[dict] = []
        self.dd: list[dict] = []          # {text, attrs, where}
        self.epoch: dict | None = None
        self.epoch_text = ""
        self.prov_labels: list[str] = []
        self._collect: list[tuple[str, dict]] = []  # (kind, holder) for text capture
        self.in_style = False
        self.style_text = ""

    def _inside(self, pred) -> bool:
        return any(pred(t, a) for t, a in self.stack)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.stack.append((tag, a))
        if tag == "style":
            self.in_style = True
        if tag == "link" and a.get("rel") == "stylesheet" and "liceu-design-tokens" in (a.get("href") or ""):
            self.token_links.append(a)
        in_panel = self._inside(lambda t, x: x.get("id") == "john-panel")
        in_drawer = self._inside(lambda t, x: t == "aside" and x.get("class", "").startswith("drawer"))
        if tag == "button" and in_panel:
            holder = {"attrs": a, "text": ""}
            self.panel_buttons.append(holder)
            self._collect.append(("button", holder))
        if tag == "dd" and (in_panel or in_drawer):
            holder = {"attrs": a, "text": "", "where": "panel" if in_panel else "drawer"}
            self.dd.append(holder)
            self._collect.append(("dd", holder))
        if tag == "div" and "epoch" in (a.get("class") or "").split():
            self.epoch = a
            self._collect.append(("epoch", {"text": ""}))
        if tag == "i" and self._inside(lambda t, x: t == "div" and "pv" in (x.get("class") or "").split()):
            holder = {"text": ""}
            self._collect.append(("prov", holder))
            self.prov_labels.append(holder)  # type: ignore[arg-type]

    def handle_endtag(self, tag):
        # fecha coletas cujo tag terminou
        while self._collect and self._collect[-1][0] in ("button", "dd", "epoch", "prov") and tag in ("button", "dd", "div", "i"):
            kind, holder = self._collect[-1]
            if (kind == "button" and tag == "button") or (kind == "dd" and tag == "dd") \
               or (kind == "epoch" and tag == "div") or (kind == "prov" and tag == "i"):
                self._collect.pop()
                if kind == "epoch":
                    self.epoch_text = holder["text"]
            else:
                break
        if tag == "style":
            self.in_style = False
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self.in_style:
            self.style_text += data
        for _, holder in self._collect:
            holder["text"] += data


def main() -> int:
    # Console Windows (cp1252) nao imprime travessao/seta; a CI e utf-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    html = INDEX.read_text(encoding="utf-8")
    p = Shell()
    p.feed(html)
    errors: list[str] = []

    # 1. tokens: consumidos por tag, nunca definidos localmente
    defined = re.findall(r"--liceu-[\w-]+\s*:", p.style_text)
    if defined:
        errors.append(f"tokens DEFINIDOS localmente (copiar e proibido): {sorted(set(defined))}")
    if not p.token_links:
        errors.append("nenhum <link rel=stylesheet> apontando para liceu-design-tokens")
    for link in p.token_links:
        href = link.get("href", "")
        if not re.search(r"liceu-design-tokens@v\d+\.\d+\.\d+/dist/tokens\.css$", href):
            errors.append(f"tokens sem TAG fixada: {href}")
    used = set(re.findall(r"var\(--liceu-[\w-]+\)", html))
    if len(used) < 10:
        errors.append(f"poucos tokens consumidos ({len(used)}); o shell deveria viver dos tokens")

    # 2. R01 / P03: painel do JOHN le ou transfere; nunca autoriza/executa
    if not p.panel_buttons:
        errors.append("painel do JOHN sem botoes (esperado: 4 de leitura + 1 de transferencia)")
    reads, transfers = 0, 0
    for b in p.panel_buttons:
        a, text = b["attrs"], " ".join(b["text"].split())
        if FORBIDDEN_VERBS.search(text) or FORBIDDEN_VERBS.search(a.get("aria-label", "")):
            errors.append(f"R01/P03: botao do painel do JOHN com verbo de autoridade/execucao: {text!r}")
        if "data-read" in a:
            reads += 1
            if a["data-read"] not in ALLOWED_READ:
                errors.append(f"data-read desconhecido: {a['data-read']!r}")
        elif "data-transfer" in a:
            transfers += 1
            if a["data-transfer"] not in ALLOWED_TRANSFER:
                errors.append(f"data-transfer desconhecido: {a['data-transfer']!r}")
            if "→" not in text and "transfere" not in text.lower():
                errors.append(f"botao de transferencia sem indicar para quem transfere: {text!r}")
        else:
            errors.append(f"botao do painel sem classificacao data-read/data-transfer: {text!r}")
        if a.get("type", "button") == "submit" or "formaction" in a:
            errors.append(f"botao do painel submete formulario: {text!r}")
    if reads != 4 or transfers != 1:
        errors.append(f"painel do JOHN: esperado 4 leitura + 1 transferencia, encontrado {reads}+{transfers}")

    # 3. R02 / R05: vazio e travessao (ou zero literal), nunca exemplo
    for d in p.dd:
        text = " ".join(d["text"].split())
        if "data-value" in d["attrs"]:
            continue
        if text not in ("—", "0"):
            errors.append(f"R02/R05 ({d['where']}): campo sem dado exibindo {text!r} em vez de travessao")
        if "none" not in (d["attrs"].get("class") or "").split():
            errors.append(f"R05 ({d['where']}): campo vazio sem classe .none (cor blocked): {text!r}")

    # 4. R04: epoca so mostra numero quando estabelecida
    if p.epoch is None:
        errors.append("chip de authority_epoch ausente na topbar")
    else:
        established = p.epoch.get("data-established") == "true"
        has_number = bool(re.search(r"\d", p.epoch_text.replace("authority_epoch", "")))
        if has_number and not established:
            errors.append(f"R04: authority_epoch mostra numero sem data-established=true: {p.epoch_text!r}")
        if not has_number and established:
            errors.append("R04: data-established=true sem numero de epoca")

    # 5. R07: barra de proveniencia com os cinco campos
    labels = [" ".join(h["text"].split()) for h in p.prov_labels]
    for field in PROV_FIELDS:
        if field not in labels:
            errors.append(f"R07: barra de proveniencia sem o campo {field!r} (tem {labels})")

    if errors:
        for e in errors:
            print("ERRO", e)
        return 1
    print(f"OK tokens por tag ({len(used)} consumidos, 0 definidos) · painel do JOHN {reads} leitura + {transfers} transferencia, "
          f"0 verbos de autoridade · {len(p.dd)} campos vazios em travessao · epoca nao estabelecida sem numero · proveniencia {len(labels)}/5")
    return 0


if __name__ == "__main__":
    sys.exit(main())
