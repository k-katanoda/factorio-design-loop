#!/usr/bin/env python3
"""Build a provisional, externally acid-fed ore mining layout (not deployable)."""
from copy import deepcopy
from pathlib import Path
import loop

ROOT = Path(__file__).resolve().parent

def build():
    data = loop.load(ROOT / 'designs/nuclear_uranium_ore_candidate.txt')
    source = loop.load(ROOT / 'designs/uranium_miners_source.txt')['blueprint_book']['blueprints'][0]['blueprint']
    source_entities = {e['entity_number']:e for e in source['entities']}
    entities = data['blueprint']['entities']
    wires = data['blueprint'].setdefault('wires', [])
    next_id = max(e['entity_number'] for e in entities)
    def add(name,x,y,d=None):
        nonlocal next_id
        next_id += 1
        e={'entity_number':next_id,'name':name,'position':{'x':x,'y':y}}
        if d is not None: e['direction']=d
        entities.append(e)
        return next_id
    # The two opposed source miners and their central belt, rotated 90 degrees.
    # Circuit shutdown and modules are omitted; they require source equipment.
    for source_id in (17,23,39):
        e=deepcopy(source_entities[source_id])
        p=e['position']
        e['position']={'x':-p['y']-25.5,'y':p['x']-252.5}
        e['direction']=(e.get('direction',0)*2+4)%16
        for key in ('control_behavior','connections','items'): e.pop(key,None)
        next_id+=1; e['entity_number']=next_id; entities.append(e)
    # External acid input continues at x=-18.5, y=-257.5.
    for y in (-259.5,-258.5,-257.5,-256.5,-255.5): add('pipe',-18.5,y)
    p1=add('medium-electric-pole',-25.5,-265.5)
    p2=add('medium-electric-pole',-18.5,-262.5)
    p3=add('medium-electric-pole',-16.5,-255.5)
    wires.extend([[1117,5,p1,5],[p1,5,p2,5],[p2,5,p3,5]])
    # An independent iron drill on a hypothetical iron patch.
    add('electric-mining-drill',-44.5,-233.5,4)
    add('express-transport-belt',-42.5,-233.5,4)
    add('express-transport-belt',-41.5,-233.5,4)
    # Experimental oil / acid area. Fluid port indexing is based on 2.0
    # prototype data; actual import and operation remain unverified.
    acid_source=loop.load(ROOT/'designs/sulfuric_acid_nilaus_source.txt')['blueprint_book']['blueprints'][1]['blueprint']
    recipes={e['recipe'] for e in acid_source['entities'] if e.get('recipe')}
    if not {'sulfur','sulfuric-acid'} <= recipes:
        raise ValueError('Unexpected chemical source')
    def machine(name,x,y,recipe):
        i=add(name,x,y,0); entities[-1]['recipe']=recipe; return i
    machine('chemical-plant',-11.5,-272.5,'sulfuric-acid')
    machine('chemical-plant',-7.5,-272.5,'sulfur')
    machine('oil-refinery',0.5,-278.5,'basic-oil-processing')
    add('pumpjack',0.5,-273.5,0)
    add('electric-furnace',-15.5,-272.5)
    add('electric-mining-drill',-15.5,-277.5,8)
    add('transport-belt',-15.5,-275.5,8)
    add('inserter',-15.5,-274.5,8)
    add('inserter',-13.5,-272.5,4)
    add('inserter',-9.5,-272.5,12)
    # Water is an external input, petroleum gas follows its separate route.
    for x in (-12.5,-11.5,-10.5,-9.5,-8.5): add('pipe',x,-274.5)
    for y in (-275.5,-276.5,-277.5): add('pipe',-9.5,y)
    add('offshore-pump',-9.5,-278.5,0)
    for x in (-6.5,-5.5,-4.5,-3.5,-2.5,-1.5): add('pipe',x,-282.5)
    for y in range(-281,-273): add('pipe',-6.5,y-0.5)
    # Basic processing explicitly uses fluidbox 3: the first (west) output.
    add('pipe',-1.5,-281.5)
    add('pipe',1.5,-275.5)
    # Acid output joins the mining supply; all terrain is hypothetical.
    for x in (-12.5,-13.5,-14.5,-15.5,-16.5,-17.5): add('pipe',x,-270.5)
    for y in range(-269,-258): add('pipe',-17.5,y-0.5)
    add('pipe',-18.5,-270.5)
    add('storage-tank',-20.5,-270.5)
    a=add('medium-electric-pole',-23.5,-269.5)
    b=add('medium-electric-pole',-14.5,-269.5)
    c=add('medium-electric-pole',-17.5,-277.5)
    d=add('medium-electric-pole',-5.5,-270.5)
    e=add('medium-electric-pole',-2.5,-272.5)
    f=add('medium-electric-pole',-1.5,-274.5)
    g=add('medium-electric-pole',-9.5,-270.5)
    wires.extend([[1223,5,a,5],[a,5,b,5],[b,5,c,5],[d,5,e,5],[e,5,f,5],[b,5,g,5],[g,5,d,5]])
    data['blueprint']['label']='EXPERIMENTAL mining and acid (hypothetical terrain)'
    return data

if __name__=='__main__':
    loop.save(ROOT/'designs/nuclear_mining_provisional.txt',build())
