#!/usr/bin/env python3
"""Factorio design loop pilot: patch, check static fluid graph, compare, export.

Only the seven fluid entities below are modelled. This is NOT a game-engine
simulation and must never be reported as proof of operational performance.
"""
from __future__ import annotations
import argparse
import base64
from collections import Counter, defaultdict, deque
import copy
import json
import hashlib
from pathlib import Path
import zlib
from urllib.parse import quote

# Dirs: 0 north, 4 east, 8 south, 12 west
VEC = {0:(0,-1),4:(1,0),8:(0,1),12:(-1,0)}
# Connection specs in NORTH-facing local coordinates: [dx,dy,outward_dir,box_id]
# Types with multiple fluid boxes must NOT shortcut through the entity.
FOOTPRINTS = {
 'pipe':(1,1),'pipe-to-ground':(1,1),'heat-pipe':(1,1),
 'storage-tank':(3,3),'heat-exchanger':(3,2),'steam-turbine':(3,5),
 'nuclear-reactor':(5,5),
}

P = {
 'pipe':[(0,0,0,'main'),(0,0,4,'main'),(0,0,8,'main'),(0,0,12,'main')],
 'pipe-to-ground':[(0,0,0,'main')],
 'storage-tank':[(-1,-1,0,'main'),(1,1,4,'main'),(1,1,8,'main'),(-1,-1,12,'main')],
 'heat-exchanger':[(-1,.5,12,'water'),(1,.5,4,'water'),(0,-.5,0,'steam')],
 'steam-turbine':[(0,-2,0,'steam'),(0,2,8,'steam')],
 # Offshore-pump is shore-aligned rather than tile-centred; this is a
 # restricted placement model for vanilla 2.0, not a general prototype loader.
 'offshore-pump':[(0,.5,8,'water')],
}

def decode(bp_text):
    s = bp_text.lstrip('\ufeff \n\r\t')
    if s.startswith('0') and not s.startswith('{'):
        return json.loads(zlib.decompress(base64.b64decode(s[1:])))
    return json.loads(s)

def encode(data):
    return '0' + base64.b64encode(zlib.compress(json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode())).decode()

def load(path): return decode(Path(path).read_text(encoding='utf-8-sig'))
def save(path,data): Path(path).write_text(encode(data)+'\n',encoding='utf-8')

def entities(data):
    if 'blueprint' not in data: raise ValueError('Only a single blueprint is supported; select an entry from a blueprint_book first.')
    return data['blueprint'].setdefault('entities',[])

def rotate(x,y,d):
    for _ in range((d//4)%4): x,y=-y,x
    return x,y

def q(v): return round(v*2)

def build_graph(es):
    # Each entry is (entity_number, box_id) and maintains separate fluid boxes.
    adj = defaultdict(set)
    surface = defaultdict(list)
    ports_by_node = defaultdict(list)
    all_ports = []
    underground=[]
    unsupported = Counter()
    for e in es:
        name=e['name']; idx=e['entity_number']; d=e.get('direction',0)
        if name not in P:
            # these are NOT failures: other parts of the plant are outside scope
            if name not in ('heat-pipe','nuclear-reactor'):unsupported[name]+=1
            continue
        if d%4: unsupported[f'{name}:noncardinal_direction']+=1;continue
        for px,py,pd,box in P[name]:
            xx,yy=rotate(px,py,d)
            x=q(e['position']['x']+xx); y=q(e['position']['y']+yy)
            direction=(pd+d)%16
            node=(idx,box); adj[node] # ensure isolated nodes are visible
            p=(node,(x,y),direction,name)
            surface[(x,y)].append(p); ports_by_node[node].append(p); all_ports.append(p)
        if name=='pipe-to-ground':
            # Game underground opening is opposite to the exposed opening.
            tunnel_dir=(d+8)%16
            underground.append((idx,(q(e['position']['x']),q(e['position']['y'])),tunnel_dir))
    for node,(x,y),direction,name in all_ports:
        dx,dy=VEC[direction]; target=(x+dx*2,y+dy*2)
        for other,xy,d2,n2 in surface.get(target,[]):
            if other!=node and d2==(direction+8)%16:
                adj[node].add(other);adj[other].add(node)
    # Nearest compatible underground endpoint, matching mutually, <=10 gap tiles
    def nearest(src):
        idx,(x,y),d=src; dx,dy=VEC[d]
        candidates=[]
        for other,(ox,oy),od in underground:
            if other==idx or od!=(d+8)%16:continue
            vx=ox-x;vy=oy-y
            if dx and vy!=0:continue
            if dy and vx!=0:continue
            length=(vx*dx+vy*dy)//2
            if 1<=length<=11 and vx==dx*2*length and vy==dy*2*length:
                candidates.append((length,other))
        return min(candidates)[1] if candidates else None
    by_id={x[0]:x for x in underground}
    pairs=[];unpaired=[]
    for u in underground:
        other=nearest(u)
        if other is None:unpaired.append(u[0]);continue
        if nearest(by_id[other]) !=u[0]:unpaired.append(u[0]);continue
        edge=tuple(sorted((u[0],other)))
        if edge not in pairs:pairs.append(edge)
        a=(u[0],'main');b=(other,'main');adj[a].add(b);adj[b].add(a)
    return adj,ports_by_node,pairs,unpaired,unsupported

def walk(adj, seeds):
    seen=set(seeds); pending=list(seeds)
    while pending:
        for nxt in adj.get(pending.pop(),()):
            if nxt not in seen: seen.add(nxt); pending.append(nxt)
    return seen

def check_geometry(es):
    occupied={}; errors=[]
    for e in es:
        name=e['name']
        if name not in FOOTPRINTS: continue
        w,h=FOOTPRINTS[name]
        direction=e.get('direction',0)
        if direction%4: continue
        if direction%8==4:w,h=h,w
        px=e['position']['x'];py=e['position']['y']
        # The entity centre is integer for even extents and .5 for odd.
        if abs((px-w/2)-round(px-w/2))>1e-7 or abs((py-h/2)-round(py-h/2))>1e-7:
            errors.append(f'Invalid footprint centre for entity #{e["entity_number"]} {name}: {px},{py} at {w}x{h}')
            continue
        x0=round(px-w/2);y0=round(py-h/2)
        for y in range(y0,y0+h):
            for x in range(x0,x0+w):
                k=(x,y)
                if k in occupied:
                    errors.append(f'Overlapping footprint: #{e["entity_number"]} {name} vs #{occupied[k]} at tile {x},{y}')
                else: occupied[k]=e['entity_number']
    return errors

def inspect(data):
    es=entities(data)
    adj,ports,pairs,unpaired,unsupported=build_graph(es)
    pumps=[(e['entity_number'],'water') for e in es if e['name']=='offshore-pump']
    water_targets=[(e['entity_number'],'water') for e in es if e['name']=='heat-exchanger']
    steam_sources=[(e['entity_number'],'steam') for e in es if e['name']=='heat-exchanger']
    steam_targets=[(e['entity_number'],'steam') for e in es if e['name']=='steam-turbine']
    water_reachable=walk(adj,pumps)
    steam_reachable=walk(adj,steam_sources)
    missing_water=[n[0] for n in water_targets if n not in water_reachable]
    missing_steam=[n[0] for n in steam_targets if n not in steam_reachable]
    # Groups of terminals, not just one merged source: a turbine must have
    # a heat-exchanger reachable in its particular component.
    mixed=[n for n in water_targets if n in steam_reachable]
    # One source and disconnected source networks are also detected.
    errors=check_geometry(es);warnings=[]
    if not pumps: warnings.append('No offshore pump in blueprint: water may be supplied from outside the selection.')
    if not water_targets: warnings.append('No heat exchanger: no water terminals to test.')
    if missing_water: errors.append(f'{len(missing_water)} of {len(water_targets)} heat-exchanger water inputs not reachable from offshore pumps.')
    if missing_steam: errors.append(f'{len(missing_steam)} of {len(steam_targets)} turbines not reachable from any heat-exchanger steam output.')
    if unpaired: errors.append(f'{len(unpaired)} pipe-to-ground endpoints without reciprocal nearby partners.')
    if mixed:errors.append('Water inputs and steam outputs appear in one connected component; check cross-fluid connections.')
    if unsupported:warnings.append(f'Unsupported prototype/direction types: {dict(unsupported)}')
    warnings.append('Heat conduction, terrain, nuclear fuel logistics and real fluid throughput are NOT simulated.')
    # Ports that do not find a direct neighbour (not necessarily defective).
    records=[]
    for e in es:
        if e['name'] not in P:continue
        node=(e['entity_number'],'water' if e['name']=='offshore-pump' else 'main')
        if e['name']=='heat-exchanger':node=(e['entity_number'],'water')
        if e['name']=='steam-turbine':node=(e['entity_number'],'steam')
        if e['name']=='offshore-pump' and not adj.get(node):
            records.append({'id':e['entity_number'],'name':e['name'],'position':e['position'],'issue':'no-adjacent-pipe'})
    return {'status':'FAIL' if errors else 'PASS_STATIC_LIMITED','entity_count':len(es),
            'fluid_model':'subset: pipe / underground pipe / storage tank / offshore pump / heat exchanger / steam turbine',
            'geometry_errors':[e for e in errors if 'footprint' in e],
            'fluid_nodes':len(adj),'underground_pairs':len(pairs),'underground_unpaired':unpaired,
            'water':{'sources':len(pumps),'inputs':len(water_targets),'reachable':len(water_targets)-len(missing_water),'unreachable_ids':missing_water},
            'steam':{'sources':len(steam_sources),'turbines':len(steam_targets),'reachable':len(steam_targets)-len(missing_steam),'unreachable_ids':missing_steam},
            'errors':errors,'warnings':warnings,'diagnostics':records}

def read_patch(path):return json.loads(Path(path).read_text(encoding='utf-8'))

def patch_data(data,patch):
    # Patch runs only against the stated baseline hash and exact entity ids;
    # aborted errors leave input untouched.
    es=entities(data)
    if patch.get('base_sha256'):
        sha=hashlib.sha256(encode(data).encode()).hexdigest()
        if patch['base_sha256'] != sha:raise ValueError('Patch baseline SHA mismatch: aborting to protect the current design')
    changes=[]
    for op in patch['operations']:
        kind=op['op'];idx=op.get('id')
        item=next((e for e in es if e.get('entity_number')==idx),None)
        if kind=='remove':
            if item is None:raise ValueError(f'No entity_number {idx}')
            if op.get('expect_name') and op['expect_name']!=item['name']:raise ValueError('Precondition failed: entity name')
            if op.get('expect_position') and op['expect_position']!=item['position']:raise ValueError('Precondition failed: position')
            es.remove(item);changes.append({'op':'remove','entity':item})
        elif kind=='update':
            if item is None:raise ValueError(f'No entity_number {idx}')
            if op.get('expect_name') and op['expect_name']!=item['name']:raise ValueError('Precondition failed: entity name')
            if op.get('expect_position') and op['expect_position']!=item['position']:raise ValueError('Precondition failed: position')
            before=copy.deepcopy(item)
            for k,v in op['set'].items():
                if k=='entity_number':raise ValueError('Cannot change id')
                item[k]=v
            changes.append({'op':'update','before':before,'after':copy.deepcopy(item)})
        elif kind=='add':
            new=copy.deepcopy(op['entity'])
            if 'entity_number' not in new:new['entity_number']=max((e['entity_number'] for e in es),default=0)+1
            if any(e['entity_number']==new['entity_number'] for e in es):raise ValueError('Duplicate entity_number')
            es.append(new);changes.append({'op':'add','entity':new})
        else:raise ValueError(f'Unsupported operation: {kind}')
    return data,changes

def diff_data(a,b):
    aa={e['entity_number']:e for e in entities(a)};bb={e['entity_number']:e for e in entities(b)}
    return {'added':[bb[i] for i in sorted(bb.keys()-aa.keys())],
            'removed':[aa[i] for i in sorted(aa.keys()-bb.keys())],
            'updated':[{'before':aa[i],'after':bb[i]} for i in sorted(aa.keys() & bb.keys()) if aa[i]!=bb[i]]}

def viewer_links(data):
    s=encode(data)
    return {
      'factorio_tools':'https://malte9799.github.io/FactorioTools/#/blueprint-editor?bp='+quote(s,safe=''),
      'factorygamefan':'https://fbe.factorygamefan.com/#source='+quote(s,safe='')
    }

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    v=sub.add_parser('validate');v.add_argument('blueprint');v.add_argument('--out')
    p=sub.add_parser('patch');p.add_argument('blueprint');p.add_argument('patch');p.add_argument('output')
    d=sub.add_parser('diff');d.add_argument('before');d.add_argument('after');d.add_argument('--out')
    l=sub.add_parser('links');l.add_argument('blueprint');l.add_argument('--out')
    args=parser.parse_args()
    if args.command=='validate':result=inspect(load(args.blueprint))
    elif args.command=='diff':result=diff_data(load(args.before),load(args.after))
    elif args.command=='links':result=viewer_links(load(args.blueprint))
    else:
        data=load(args.blueprint)
        data,changes=patch_data(data,read_patch(args.patch));save(args.output,data)
        result={'new_blueprint':args.output,'changes':changes,'validation':inspect(data)}
    txt=json.dumps(result,ensure_ascii=False,indent=2)
    if getattr(args,'out',None):Path(args.out).write_text(txt+'\n',encoding='utf-8')
    print(txt)
    if args.command=='validate' and result['status']=='FAIL':return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
