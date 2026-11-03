#!/usr/bin/env python3
"""Add a conservatively sized full-sun startup supply to the candidate."""
from pathlib import Path
import loop

ROOT=Path(__file__).resolve().parent
PANELS=200
ACCUMULATORS=1

def build():
    data=loop.load(ROOT/'designs/nuclear_mining_provisional.txt')
    bp=data['blueprint']; entities=bp['entities']; wires=bp.setdefault('wires',[])
    n=max(e['entity_number'] for e in entities)
    def add(name,x,y):
        nonlocal n
        n+=1; entities.append({'entity_number':n,'name':name,'position':{'x':x,'y':y}}); return n
    # Each 18x18 area is powered by one substation; the rightmost substation
    # is wired to the existing uranium processing network.
    grid={}
    for y in (-295,-277,-259):
        for x in (-97,-79): grid[(x,y)]=add('substation',x,y)
    add('accumulator',-85,-295)
    # Uranium ore input inserter 1045 was outside the previous pole coverage.
    inlet_pole=add('medium-electric-pole',-22.5,-255.5)
    wires.append([1224,5,inlet_pole,5])
    wires.append([1131,5,grid[(-79,-259)],5])
    for y in (-295,-277,-259): wires.append([grid[(-97,y)],5,grid[(-79,y)],5])
    for x in (-97,-79):
        for a,b in [(-295,-277),(-277,-259)]: wires.append([grid[(x,a)],5,grid[(x,b)],5])
    # A panel is removed wherever a substation or accumulator occupies its
    # footprint. Fill the remaining slots in a deterministic order.
    def overlaps(x,y,ox,oy,half):
        return abs(x-ox)<1.5+half and abs(y-oy)<1.5+half
    count=0
    for y in (-295,-277,-259):
        for x in (-79,-97):
            for dy in (-6.5,-3.5,-.5,2.5,5.5,8.5):
                for dx in (-6.5,-3.5,-.5,2.5,5.5,8.5):
                    px,py=x+dx,y+dy
                    if overlaps(px,py,x,y,1) or overlaps(px,py,-85,-295,1): continue
                    if count<PANELS: add('solar-panel',px,py); count+=1
    if count!=PANELS: raise ValueError(f'Insufficient panel slots: {count}')
    bp['label']='EXPERIMENTAL mining and acid + full sun startup power'
    return data

if __name__=='__main__':
    loop.save(ROOT/'designs/nuclear_solar_startup_candidate.txt',build())
