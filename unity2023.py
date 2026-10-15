"""Project-bound launcher for upstream unity-cli. No mutation retries or implicit upgrades."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parent
DEFAULT_CLI=ROOT/'unity-cli.exe'

def embedded_error(value):
    if isinstance(value,dict):
        if value.get('success') is False:return value
        if value.get('error'):return value['error']
        if value.get('errors'):return value['errors']
        if value.get('requestId') and value.get('state')!='completed':
            return value
    return None

def run(cli,project,tail,timeout_ms=15000):
    env=os.environ.copy()
    for key in ('UNITY_CLI_PORT','UNITY_CLI_HOST','UNITY_PROJECT_ROOT'):env.pop(key,None)
    env['UNITY_CLI_NO_AUTO_UPDATE']='1'
    args=[str(cli),'--project-path',str(project),'--output','json','--timeout-ms',str(timeout_ms),*tail]
    try:
        p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',env=env,timeout=timeout_ms/1000+20)
    except subprocess.TimeoutExpired as exc:
        return {'success':False,'error':'CLIENT_TIMEOUT','executionState':'unknown','message':'The Editor may still be executing. Inspect state/result; do not retry a write.','command':tail},3
    try:d=json.loads(p.stdout)
    except json.JSONDecodeError:
        return {'success':False,'error':'INVALID_CLI_RESPONSE','exitCode':p.returncode,'stdout':p.stdout,'stderr':p.stderr},2
    problem=embedded_error(d) or embedded_error(d.get('data'))
    if problem and d.get('success') is True:
        d={'success':False,'error':'EDITOR_OPERATION_FAILED','details':problem,'upstream':d}
    return d,0 if p.returncode==0 and not problem else (p.returncode or 2)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--cli',type=Path,default=DEFAULT_CLI)
    p.add_argument('--timeout-ms',type=int,default=15000)
    p.add_argument('--state-dir',type=Path,default=Path(os.environ.get('LOCALAPPDATA',str(ROOT)))/'UnityCLI2023/Requests')
    sub=p.add_subparsers(dest='command',required=True)
    for name in ('status','doctor','capabilities','tools','open','close'):sub.add_parser(name)
    x=sub.add_parser('schema');x.add_argument('name')
    x=sub.add_parser('call');x.add_argument('name');x.add_argument('--params-file',type=Path)
    x=sub.add_parser('eval');x.add_argument('--file',type=Path,required=True);x.add_argument('--request-id',default=None);x.add_argument('--mode',choices=['expression','statements'],default='statements')
    x=sub.add_parser('eval-status');x.add_argument('request_id')
    x=sub.add_parser('wait');x.add_argument('--seconds',type=int,default=120)
    args=p.parse_args();project=args.project.resolve()
    if not (project/'ProjectSettings/ProjectVersion.txt').is_file():p.error('Not a Unity project')
    if not args.cli.is_file():p.error('Pinned unity-cli executable not found')
    if args.timeout_ms<1:p.error('timeout-ms must be positive')
    if args.command=='open' and (project/'.pvzmc-main-write-lease.json').exists():
        print(json.dumps({'success':False,'error':'PROJECT_WRITER_LEASE_PRESENT','message':'Another project writer may own this project. Wait for its normal release before opening the Editor.'}));return 2
    mapping={'status':['editor','status'],'doctor':['doctor'],'capabilities':['tool','call','unity2023_capabilities'],'tools':['tool','list'],'open':['editor','open'],'close':['editor','close']}
    if args.command in mapping:tail=mapping[args.command]
    elif args.command=='schema':tail=['tool','schema',args.name]
    elif args.command=='call':
        tail=['tool','call',args.name]
        if args.params_file:
            json.loads(args.params_file.read_text(encoding='utf-8-sig'))
            tail+=['--params-file',str(args.params_file.resolve())]
    elif args.command=='eval':
        request_id=args.request_id or 'u2023-'+uuid.uuid4().hex
        if not request_id or len(request_id)>128 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in request_id):
            p.error('request-id must contain 1-128 ASCII letters, digits, underscores or hyphens')
        code=args.file.read_text(encoding='utf-8-sig')
        request_key=hashlib.sha256((os.path.normcase(str(project))+'\n'+request_id).encode('utf-8')).hexdigest()
        args.state_dir.mkdir(parents=True,exist_ok=True)
        journal=args.state_dir/(request_key+'.json')
        entry={'requestId':request_id,'project':str(project),'mode':args.mode,'source':code,'sourceSha256':hashlib.sha256(code.encode('utf-8')).hexdigest(),'submittedAtUtc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'state':'pending','warning':'A client/domain timeout is not proof of no side effects; query this ID and inspect authoritative output. Never resubmit this ID.'}
        try:
            with journal.open('x',encoding='utf-8') as stream:json.dump(entry,stream,ensure_ascii=False,indent=2)
        except FileExistsError:
            result,code_status=run(args.cli,project,['editor','eval-status',request_id],args.timeout_ms)
            print(json.dumps({'success':False,'error':'REQUEST_ALREADY_SUBMITTED','requestId':request_id,'journal':str(journal),'status':result,'message':'This invocation did not submit eval again, even if domain status is unknown. Inspect the original side effects.'},ensure_ascii=False,indent=2));return 3
        print('eval request-id: '+request_id+' (query this ID after timeout; never repeat with a fresh ID)',file=sys.stderr)
        tail=['editor','eval',code,'--mode',args.mode,'--request-id',request_id]
    elif args.command=='eval-status':tail=['editor','eval-status',args.request_id]
    else:
        started=time.monotonic()
        while True:
            result,code=run(args.cli,project,['system','ping'],min(args.timeout_ms,5000))
            if code==0 or time.monotonic()-started>=args.seconds:break
            time.sleep(2)
        print(json.dumps(result,ensure_ascii=False,indent=2));return code
    result,code=run(args.cli,project,tail,args.timeout_ms)
    if args.command=='eval':
        actual_state=result.get('data',{}).get('state') if isinstance(result.get('data'),dict) else None
        if actual_state is None and isinstance(result.get('upstream'),dict):
            actual_state=result['upstream'].get('data',{}).get('state')
        entry.update(state='completed' if code==0 and actual_state=='completed' else 'failed-or-unknown',editorResultState=actual_state,result=result)
        journal.write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding='utf-8')
    if args.command=='capabilities' and code==0:
        actual=Path(result['data']['projectPath']).resolve()
        if os.path.normcase(str(actual))!=os.path.normcase(str(project)):
            result={'success':False,'error':'WRONG_PROJECT','expected':str(project),'actual':str(actual)};code=2
    print(json.dumps(result,ensure_ascii=False,indent=2));return code

if __name__=='__main__':
    try:sys.exit(main())
    except (OSError,ValueError,KeyError) as exc:
        print(json.dumps({'success':False,'error':type(exc).__name__,'message':str(exc)},ensure_ascii=False));sys.exit(2)
