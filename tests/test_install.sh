#!/bin/bash
# בדיקת מסלול ההתקנה המלא בהגדרות Claude Code זמניות (CLAUDE_CONFIG_DIR) ובבית זמני — לא נוגע בהגדרות האמיתיות.
#   bash tests/test_install.sh <git source of this repo> "<copy of an Uno Studio folder>" <old tag> <new tag>
# בודק: התקנה נקייה, רשימת כלים, קריאת פרויקט, פעולה הפיכה על עותק, סגירה/פתיחה, התקנה שנייה, שדרוג, חזרה,
# שחיבור MCP אחר נשאר ושהקאטים הקיימים לא השתנו.
set -uo pipefail
SRC="$1"; UNO="$2"; OLD="$3"; NEW="$4"; HERE="$(cd "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /private/tmp/uno-connector-test.XXXX)"; export CLAUDE_CONFIG_DIR="$T/cfg"; H="$T/home"; mkdir -p "$CLAUDE_CONFIG_DIR" "$H/Downloads"
cp -cR "$UNO" "$H/Downloads/Uno Studio" 2>/dev/null || cp -R "$UNO" "$H/Downloads/Uno Studio"
export UNO_CONNECTOR_NO_SPOTLIGHT=1; unset UNO_STUDIO_ROOT
pass=0; fail=0; ok(){ if [ "$1" = 0 ]; then echo "PASS $2"; pass=$((pass+1)); else echo "FAIL $2"; fail=$((fail+1)); fi; }
claude mcp add --scope user other-mcp -- python3 -c "print(1)" >/dev/null 2>&1
CUTS0=$(md5 -q "$H/Downloads/Uno Studio/projects/"*.json | sort | tr '\n' ' ')
inst(){ HOME="$H" bash "$HERE/install.sh" --source "$SRC" "$@" > "$T/last.log" 2>&1; }
probe(){ HOME="$H" python3 - "$1" <<'PY'
import json,subprocess,sys,os
p=subprocess.Popen(["python3",sys.argv[1]],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
n=[0]
def call(m,pa=None):
    n[0]+=1; p.stdin.write(json.dumps({"jsonrpc":"2.0","id":n[0],"method":m,**({"params":pa} if pa is not None else {})})+"\n"); p.stdin.flush()
    while True:
        d=json.loads(p.stdout.readline())
        if d.get("id")==n[0]: return d
call("initialize",{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"t","version":"1"}})
tools=[t["name"] for t in call("tools/list")["result"]["tools"]]
projs=[x["name"] for x in json.loads(call("tools/call",{"name":"list_projects","arguments":{}})["result"]["content"][0]["text"])["projects"]]
cut=json.loads(call("tools/call",{"name":"read_cut","arguments":{"name":projs[0]}})["result"]["content"][0]["text"])
r=call("tools/call",{"name":"add_layers","arguments":{"name":projs[0],"new_name":"__connector_test","layers":[{"kind":"graphic","start":0.5,"end":1.5,"text":"test"}]}})["result"]
print(json.dumps({"tools":len(tools),"projects":len(projs),"clips":len(cut["clips"]),"copy_ok":not r.get("isError")}))
p.terminate()
PY
}
inst --version "$OLD"; ok $? "clean install $OLD"
claude mcp list 2>/dev/null | grep -q "plugin:uno-studio:uno-studio.*Connected"; ok $? "claude mcp list shows plugin:uno-studio:uno-studio connected"
PLUG="$H/.uno-studio-connector/releases/$OLD/plugins/uno-studio/connector/uno_connector.py"
R=$(probe "$PLUG"); echo "  $R"; echo "$R" | grep -q '"tools": 12, "projects": [1-9][0-9]*, "clips": [1-9][0-9]*, "copy_ok": true'; ok $? "tools, list_projects, read_cut, new copy via add_layers"
rm -f "$H/Downloads/Uno Studio/projects/__connector_test.json"; [ ! -f "$H/Downloads/Uno Studio/projects/__connector_test.json" ]; ok $? "reversible: test copy removed"
R2=$(probe "$PLUG"); rm -f "$H/Downloads/Uno Studio/projects/__connector_test.json"; echo "$R2" | grep -q '"copy_ok": true'; ok $? "close and reopen the server: works again"
inst --version "$OLD"; ok $? "second install of the same version (idempotent)"
inst; grep -q "connector\": \"${NEW#v}\"" "$T/last.log"; ok $? "upgrade to newest ($NEW)"
inst --rollback; grep -q "connector\": \"${OLD#v}\"" "$T/last.log"; ok $? "rollback to $OLD"
claude mcp list 2>/dev/null | grep -q "^other-mcp:"; ok $? "the other MCP server is still configured"
[ "$(md5 -q "$H/Downloads/Uno Studio/projects/"*.json | sort | tr '\n' ' ')" = "$CUTS0" ]; ok $? "existing cuts unchanged"
ls "$CLAUDE_CONFIG_DIR/backups" | grep -q uno-connector; ok $? "settings backed up before each change"
echo "RESULT: $pass passed, $fail failed  (temp: $T)"
[ "$fail" = 0 ]
