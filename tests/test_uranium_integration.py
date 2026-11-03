import math
import unittest

import integrate_uranium
import loop


class UraniumIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = integrate_uranium.build()
        cls.blueprint = cls.candidate['blueprint']
        cls.entities = {e['entity_number']: e for e in cls.blueprint['entities']}

    def test_candidate_is_reproducible_and_preserves_source(self):
        self.assertEqual(self.candidate, loop.load('designs/nuclear_uranium_ore_candidate.txt'))
        self.assertEqual(integrate_uranium.converted_ore_blueprint(self.candidate),
                         loop.load('designs/uranium_processing_red_2_0_candidate.txt'))
        converted = [e for e in self.entities.values() if 1040 <= e['entity_number'] <= 1204]
        self.assertEqual(len(converted), 165)
        self.assertEqual(sum(e.get('recipe') == 'uranium-processing' for e in converted), 10)
        self.assertTrue(self.entities[1045]['use_filters'])
        self.assertEqual(self.entities[1045]['filters'][0]['name'], 'uranium-ore')

    def test_separate_outputs_lead_to_existing_splitter_inputs(self):
        by_position = {(e['position']['x'], e['position']['y']): e for e in self.entities.values()
                       if e['name'] in ('transport-belt', 'fast-transport-belt', 'fast-underground-belt')}
        for position, direction in [((-28.5,-254.5),8),((-28.5,-253.5),8),((-28.5,-252.5),8),
                                    ((-24.5,-254.5),8),((-24.5,-253.5),12),((-25.5,-253.5),12),
                                    ((-26.5,-253.5),12),((-27.5,-253.5),8),((-27.5,-252.5),8),
                                    ((-27.5,-251.5),8)]:
            self.assertEqual(by_position[position].get('direction', 0), direction, position)
        self.assertEqual(self.entities[877]['filter']['name'], 'uranium-235')
        self.assertEqual(self.entities[1213]['position'], {'x':-21.5,'y':-257.5})
        self.assertEqual(self.entities[1045]['position'], {'x':-22.5,'y':-257.5})
        self.assertEqual(self.entities[1045]['direction'], 4)
        self.assertEqual(self.entities[1048]['position'], {'x':-23.5,'y':-257.5})
        self.assertEqual(self.entities[1048]['type'], 'input')
        self.assertEqual(self.entities[1048]['direction'], 12)
        self.assertEqual(self.entities[1053]['position'], {'x':-30.5,'y':-257.5})
        self.assertEqual(self.entities[1053]['type'], 'output')
        self.assertEqual(self.entities[1053]['direction'], 12)

    def test_power_bridge_uses_reachable_poles(self):
        for a,b,limit in [(1117,1125,18),(1125,1131,18),(887,1205,7.5),(1117,1205,9)]:
            self.assertTrue([a,5,b,5] in self.blueprint['wires'] or [b,5,a,5] in self.blueprint['wires'])
            p=self.entities[a]['position']; q=self.entities[b]['position']
            self.assertLessEqual(math.hypot(p['x']-q['x'], p['y']-q['y']), limit)

    def test_new_components_do_not_overlap_old_components(self):
        sizes={'nuclear-reactor':(5,5),'heat-exchanger':(3,2),'steam-turbine':(3,5),
               'storage-tank':(3,3),'substation':(2,2),'centrifuge':(3,3),
               'assembling-machine-3':(3,3),'electric-furnace':(3,3),
               'decider-combinator':(1,2),'splitter':(2,1),'fast-splitter':(2,1)}
        def rect(e):
            w,h=sizes.get(e['name'],(1,1))
            if e['name'] in ('heat-exchanger','steam-turbine','decider-combinator','splitter','fast-splitter') and e.get('direction',0)%8==4:
                w,h=h,w
            x,y=e['position']['x'],e['position']['y']
            return (x-w/2,y-h/2,x+w/2,y+h/2)
        def overlaps(a,b):
            return a[0]<b[2]-1e-9 and b[0]<a[2]-1e-9 and a[1]<b[3]-1e-9 and b[1]<a[3]-1e-9
        old=[e for e in self.entities.values() if e['entity_number']<=1039]
        source=[e for e in self.entities.values() if 1040<=e['entity_number']<=1204]
        bridges=[e for e in self.entities.values() if e['entity_number']>=1205]
        for added in source+bridges:
            for previous in old:
                self.assertFalse(overlaps(rect(added),rect(previous)), (added['entity_number'],previous['entity_number']))
        for i,added in enumerate(bridges):
            for other in source+bridges[i+1:]:
                self.assertFalse(overlaps(rect(added),rect(other)), (added['entity_number'],other['entity_number']))
