#!/usr/bin/env python3
"""Build the uranium-ore integration candidate from the retained blueprints."""
from copy import deepcopy
from pathlib import Path
import loop

ROOT = Path(__file__).resolve().parent

def build():
    data = loop.load(ROOT / 'designs/nuclear_fuel_smelter_candidate.txt')
    source = loop.load(ROOT / 'designs/uranium_processing_no_modules_red_legacy.txt')['blueprint']
    if source.get('label') != 'Uranium Processing - No Modules - Red' or len(source['entities']) != 165:
        raise ValueError('Unexpected uranium processing source')
    blueprint = data['blueprint']
    entities = blueprint['entities']
    wires = blueprint.setdefault('wires', [])
    offset = max(e['entity_number'] for e in entities)
    if offset != 1039:
        raise ValueError('Unexpected integrated baseline entity IDs')
    directional = {'fast-transport-belt', 'fast-underground-belt', 'fast-inserter', 'filter-inserter', 'fast-splitter'}
    for original in source['entities']:
        e = deepcopy(original)
        e['entity_number'] += offset
        e['position'] = {'x': -original['position']['x'] - 45.5, 'y': -original['position']['y'] - 260.5}
        if e['name'] in directional:
            e['direction'] = (original.get('direction', 0) * 2 + 8) % 16
        if e['name'] == 'filter-inserter':
            e['name'] = 'fast-inserter'
            e['use_filters'] = True
        if isinstance(e.get('filter'), str):
            e['filter'] = {'name': e['filter'], 'quality': 'normal', 'comparator': '='}
        entities.append(e)
    wires.extend([[offset+78, 5, offset+86, 5], [offset+86, 5, offset+92, 5]])
    next_id = offset + 166
    pole_id = next_id
    entities.append({'entity_number':pole_id, 'name':'medium-electric-pole', 'position':{'x':-31.5,'y':-255.5}})
    wires.extend([[887,5,pole_id,5],[offset+78,5,pole_id,5]])
    # U-235 output goes straight south. U-238 turns west and enters the other
    # side of the receiving splitter. The final belt is an external ore input.
    for x,y,d in [(-28.5,-253.5,8),(-24.5,-253.5,12),(-25.5,-253.5,12),(-26.5,-253.5,12),(-27.5,-253.5,8),(-27.5,-252.5,8),(-27.5,-251.5,8),(-21.5,-257.5,12)]:
        next_id += 1
        entities.append({'entity_number':next_id,'name':'fast-transport-belt','position':{'x':x,'y':y},'direction':d})
    blueprint['label'] = 'Nuclear x 4 + fuel processing + uranium processing (candidate)'
    return data

def converted_ore_blueprint(integrated):
    """Extract the converted source module, preserving the 2.0 placement."""
    source = loop.load(ROOT / 'designs/uranium_processing_no_modules_red_legacy.txt')['blueprint']
    entities = []
    for item in integrated['blueprint']['entities']:
        if 1040 <= item['entity_number'] <= 1204:
            e = deepcopy(item)
            e['entity_number'] -= 1039
            entities.append(e)
    return {'blueprint': {'item':'blueprint', 'label':'Uranium processing - Red (2.0 candidate)',
                          'icons':deepcopy(source['icons']), 'entities':entities,
                          'wires':[[78,5,86,5],[86,5,92,5]], 'version':(2<<48)|(76<<16)}}

if __name__ == '__main__':
    output = ROOT / 'designs/nuclear_uranium_ore_candidate.txt'
    candidate = build()
    loop.save(output, candidate)
    loop.save(ROOT / 'designs/uranium_processing_red_2_0_candidate.txt', converted_ore_blueprint(candidate))
    print('Created', output)
