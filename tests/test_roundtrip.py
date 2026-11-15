"""Install from a Git source, then edit only a copied Uno fixture over MCP."""
import hashlib
import json
import os
from pathlib import Path
import selectors
import shutil
import subprocess
import sys
import tempfile

repo, fixture = sys.argv[1:]
home = Path(tempfile.mkdtemp(prefix='uno-desktop-roundtrip-')).resolve()
root = home/'Downloads/Uno Studio'
root.parent.mkdir(parents=True)
shutil.copytree(fixture, root, symlinks=True)
cfg = home/'Library/Application Support/Claude/claude_desktop_config.json'
cfg.parent.mkdir(parents=True)
original_config={'mcpServers':{'preserved-server':{'command':'unchanged','args':['keep']}},'preferences':{'keep':True}}
cfg.write_text(json.dumps(original_config))
env=dict(os.environ,HOME=str(home),UNO_CONNECTOR_NO_SPOTLIGHT='1')
env.pop('UNO_STUDIO_ROOT',None)
installer = Path(__file__).resolve().parents[1]/'install.sh'
for _ in range(2):
    subprocess.run(['bash',str(installer),'--source',repo],env=env,check=True,stdout=subprocess.DEVNULL)
after=json.loads(cfg.read_text())
assert after['mcpServers']['preserved-server']==original_config['mcpServers']['preserved-server']
assert after['preferences']==original_config['preferences']
entry=after['mcpServers']['uno-studio']
assert Path(entry['args'][0]).is_relative_to(home)
assert not (home/'.claude/plugins').exists()
paths=list((root/'projects').glob('*.json'))
assert paths
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

def exercise(edit):
    p=subprocess.Popen([entry['command'],*entry['args']],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ)
    counter=0
    def call(method,params=None):
        nonlocal counter
        counter+=1
        p.stdin.write(json.dumps({'jsonrpc':'2.0','id':counter,'method':method,**({'params':params} if params is not None else {})})+'\n');p.stdin.flush()
        if not sel.select(25):raise RuntimeError('MCP response timed out')
        line=p.stdout.readline()
        if not line:raise RuntimeError('MCP closed: '+p.stderr.read()[-1200:])
        response=json.loads(line)
        if 'error' in response:raise RuntimeError(str(response['error']))
        result=response['result']
        if result.get('isError'):raise RuntimeError(str(result))
        return result
    def tool(name,args):return json.loads(call('tools/call',{'name':name,'arguments':args})['content'][0]['text'])
    try:
        call('initialize',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'isolated-test','version':'1'}})
        names=[t['name'] for t in call('tools/list')['tools']]
        assert 'add_layers' in names and 'read_cut' in names
        project=tool('list_projects',{})['projects'][0]['name']
        tool('read_cut',{'name':project})
        if edit:
            result=tool('add_layers',{'name':project,'new_name':'MCP isolated title proof','layers':[{'kind':'graphic','start':0.5,'end':1.5,'text':'MCP TEST'}]})
            assert result['original_unchanged']
            created=root/result['file']
            assert created.exists() and 'MCP TEST' in created.read_text()
            tool('read_cut',{'name':result['created']})
        return len(names)
    finally:
        sel.close();p.terminate();p.communicate(timeout=10)

count=exercise(True)
exercise(False)
assert all(Path(path).exists() and hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest for path,digest in before.items())
assert list((home/'.uno-studio-connector/backups').glob('*/claude_desktop_config.json'))
print(json.dumps({'result':'PASS','tools':count,'install_twice':True,'other_settings_preserved':True,'new_title_copy_verified':True,'original_cuts_unchanged':True,'reconnect':True,'no_plugin_installed':True,'evidence_home':str(home)}))
