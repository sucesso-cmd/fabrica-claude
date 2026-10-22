#!/usr/bin/env python3
"""Fábrica: instalador e atualizador (só biblioteca padrão do Python 3).

  python3 fabrica.py license --email you@co.com
  python3 fabrica.py install --email you@co.com [--dir fabrica]
  python3 fabrica.py install --email you@agency.com --client "Sunny Dental"   # plano agências: pasta fabrica-sunny-dental
  python3 fabrica.py update  [--dir fabrica]
  python3 fabrica.py numbers --file numeros.json [--dir fabrica]   # grava dados.json e liga a fonte json
  python3 fabrica.py check   [--dir fabrica]                       # confere config e dados

Install and update keep fabrica.config.js, dados.json and anything the customer changed.
"""
import argparse, io, json, os, re, shutil, sys, urllib.error, urllib.request, zipfile

SERVER = os.environ.get("FABRICA_SERVER", "https://fabrica-site-71s.pages.dev")
KEEP = {"fabrica.config.js", "dados.json", ".fabrica-licenca"}


def call(path, body=None):
    req = urllib.request.Request(SERVER + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json", "User-Agent": "fabrica-claude/1.0"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=30))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {"ok": False, "erro": f"HTTP {e.code}"}


def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:60]


def license_(email, client=None):
    body = {"email": email.strip().lower()}
    if client:
        body["client"] = client
    d = call("/api/license", body)
    if not d.get("ok"):
        sys.exit("LICENSE_FAIL: " + d.get("erro", "no active subscription"))
    return d


def download(url):
    req = urllib.request.Request(url, headers={"User-Agent": "fabrica-claude/1.0"})
    return zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(req, timeout=60).read()))


def unpack(z, dest):
    os.makedirs(dest, exist_ok=True)
    changed = []
    for name in z.namelist():
        rel = name.split("/", 1)[1] if "/" in name else name
        if not rel or rel.endswith("/"):
            continue
        target = os.path.join(dest, rel)
        if os.path.basename(rel) in KEEP and os.path.exists(target):
            continue  # nunca sobrescreve a configuração e os números do cliente
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with z.open(name) as src, open(target, "wb") as out:
            shutil.copyfileobj(src, out)
        changed.append(rel)
    return changed


def lic_file(dest):
    return os.path.join(dest, ".fabrica-licenca")


def resumo(d):
    out = {"plan": d.get("plan")}
    if d.get("plan") == "b2b":
        out.update(client=d.get("client"), clients_used=d.get("clients_used"), clients_limit=d.get("clients_limit"))
    return out


def cmd_license(a):
    d = license_(a.email, a.client)
    print(json.dumps({"ok": True, "version": d.get("version"), **resumo(d)}))


def cmd_install(a):
    if a.client and a.dir == "fabrica":
        a.dir = "fabrica-" + slug(a.client)  # uma pasta por cliente
    d = license_(a.email, a.client)
    if d.get("plan") == "b2b" and not a.client:
        sys.exit("NEED_CLIENT: agency license, run install again with --client \"Client name\"")
    files = unpack(download(d["download"]), a.dir)
    info = {"email": a.email.strip().lower(), "version": d.get("version")}
    if a.client:
        info["client"] = a.client
        for cfg in ("fabrica.config.js", "fabrica.config.en.js"):  # separa ações de vários clientes no mesmo domínio
            p = os.path.join(a.dir, cfg)
            if os.path.exists(p):
                s = open(p).read()
                open(p, "w").write(re.sub(r"chave:\s*''", "chave: '" + slug(a.client) + "'", s, count=1))
    with open(lic_file(a.dir), "w") as f:
        json.dump(info, f)
    os.chmod(os.path.join(a.dir, "iniciar.sh"), 0o755) if os.path.exists(os.path.join(a.dir, "iniciar.sh")) else None
    print(json.dumps({"ok": True, "dir": os.path.abspath(a.dir), "version": d.get("version"), "files": len(files), **resumo(d)}))


def cmd_update(a):
    if not os.path.exists(lic_file(a.dir)):
        sys.exit("NO_INSTALL: run install first")
    info = json.load(open(lic_file(a.dir)))
    d = license_(info["email"], info.get("client"))
    if d.get("version") and d.get("version") == info.get("version") and not a.force:
        print(json.dumps({"ok": True, "updated": False, "version": d.get("version")}))
        return
    files = unpack(download(d["download"]), a.dir)
    info["version"] = d.get("version")
    json.dump(info, open(lic_file(a.dir), "w"))
    print(json.dumps({"ok": True, "updated": True, "version": d.get("version"), "files": len(files)}))


def cmd_numbers(a):
    nums = json.load(open(a.file))
    payload = nums if "numeros" in nums else {"numeros": nums}
    old = os.path.join(a.dir, "dados.json")
    if os.path.exists(old):
        try:
            payload.setdefault("acoes", json.load(open(old)).get("acoes", []))
        except Exception:
            pass
    json.dump(payload, open(old, "w"), ensure_ascii=False, indent=2)
    cfg = os.path.join(a.dir, "fabrica.config.js")
    s = open(cfg).read()
    s2 = re.sub(r"tipo:\s*'(demo|planilha)'", "tipo: 'json'", s, count=1)
    if s2 != s:
        open(cfg, "w").write(s2)
    print(json.dumps({"ok": True, "keys": len(payload["numeros"])}))


def cmd_check(a):
    cfg = open(os.path.join(a.dir, "fabrica.config.js")).read()
    ids = re.findall(r"\{\s*id:\s*'([^']+)'", cfg)
    tipo = (re.search(r"tipo:\s*'(\w+)'", cfg) or [None, "?"])[1]
    out = {"ok": True, "fonte": tipo, "ids": ids, "faltando": []}
    dj = os.path.join(a.dir, "dados.json")
    if tipo == "json" and os.path.exists(dj):
        def flat(o, p=""):
            r = {}
            for k, v in o.items():
                kk = p + "." + k if p else k
                r.update(flat(v, kk) if isinstance(v, dict) else {kk: v})
            return r
        d = json.load(open(dj))
        keys = flat(d.get("numeros", d))
        for i in ids:
            if not any(k.startswith(i + ".") for k in keys):
                out["faltando"].append(i)
    print(json.dumps(out, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("license", "install", "update", "numbers", "check"):
        s = sub.add_parser(name)
        s.add_argument("--dir", default="fabrica")
        if name in ("license", "install"):
            s.add_argument("--email", required=True)
            s.add_argument("--client", help="agency plan: the client this factory is for")
        if name == "update":
            s.add_argument("--force", action="store_true")
        if name == "numbers":
            s.add_argument("--file", required=True)
    a = p.parse_args()
    {"license": cmd_license, "install": cmd_install, "update": cmd_update, "numbers": cmd_numbers, "check": cmd_check}[a.cmd](a)


if __name__ == "__main__":
    main()
