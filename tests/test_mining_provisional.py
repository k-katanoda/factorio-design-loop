import math
import unittest
import integrate_mining_candidate
import loop

class MiningCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=integrate_mining_candidate.build()
        cls.entities={e['entity_number']:e for e in cls.data['blueprint']['entities']}

    def test_reproducible_and_expected_routes(self):
        self.assertEqual(self.data,loop.load('designs/nuclear_mining_provisional.txt'))
        for i,p,d in [(1214,(-20.5,-259.5),8),(1215,(-20.5,-255.5),0),
                      (1216,(-20.5,-257.5),12),(1213,(-21.5,-257.5),12),
                      (1225,(-44.5,-233.5),4),(1226,(-42.5,-233.5),4),
                      (1227,(-41.5,-233.5),4),(1036,(-40.5,-233.5),4)]:
            e=self.entities[i]
            self.assertEqual((e['position']['x'],e['position']['y']),p)
            self.assertEqual(e.get('direction',0),d)
        self.assertEqual([(self.entities[i]['position']['x'],self.entities[i]['position']['y']) for i in range(1217,1222)],
                         [(-18.5,y) for y in (-259.5,-258.5,-257.5,-256.5,-255.5)])

    def test_pole_wire_lengths(self):
        wires=self.data['blueprint']['wires']
        for a,b in [(1117,1222),(1222,1223),(1223,1224)]:
            self.assertIn([a,5,b,5],wires)
            x,y=self.entities[a]['position'],self.entities[b]['position']
            self.assertLessEqual(math.hypot(x['x']-y['x'],x['y']-y['y']),9)

    def test_added_entities_do_not_overlap(self):
        sizes={'nuclear-reactor':(5,5),'heat-exchanger':(3,2),'steam-turbine':(3,5),
               'storage-tank':(3,3),'substation':(2,2),'centrifuge':(3,3),
               'assembling-machine-3':(3,3),'electric-furnace':(3,3),'electric-mining-drill':(3,3),
               'chemical-plant':(3,3),'pumpjack':(3,3),'oil-refinery':(5,5),
               'decider-combinator':(1,2),'splitter':(2,1),'fast-splitter':(2,1)}
        def rect(e):
            w,h=sizes.get(e['name'],(1,1))
            if e['name'] in ('heat-exchanger','steam-turbine','decider-combinator','splitter','fast-splitter') and e.get('direction',0)%8==4: w,h=h,w
            x,y=e['position']['x'],e['position']['y']
            return (x-w/2,y-h/2,x+w/2,y+h/2)
        def overlap(a,b):return a[0]<b[2]-1e-9 and b[0]<a[2]-1e-9 and a[1]<b[3]-1e-9 and b[1]<a[3]-1e-9
        for n,e in self.entities.items():
            if n<=1213: continue
            for m,f in self.entities.items():
                if m<n:self.assertFalse(overlap(rect(e),rect(f)),(n,m))

    def test_fluid_networks_are_separate_and_reach_ports(self):
        pipes={(e['position']['x'],e['position']['y']) for n,e in self.entities.items() if n>1213 and e['name']=='pipe'}
        def component(seed):
            visited={seed}; stack=[seed]
            while stack:
                x,y=stack.pop()
                for p in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if p in pipes and p not in visited: visited.add(p); stack.append(p)
            return visited
        # Water to both chemical plant inputs; oil to refinery; refinery gas
        # fluidbox 3 to sulfur's second input; acid to tank and both drills.
        groups=[{(-9.5,-277.5),(-12.5,-274.5),(-8.5,-274.5)},
                {(1.5,-275.5)},
                {(-1.5,-281.5),(-6.5,-274.5)},
                {(-12.5,-270.5),(-18.5,-270.5),(-18.5,-259.5),(-18.5,-255.5)}]
        networks=[]
        for group in groups:
            self.assertTrue(group <= pipes)
            net=component(next(iter(group)))
            self.assertTrue(group <= net)
            networks.append(net)
        for i,one in enumerate(networks):
            for two in networks[i+1:]: self.assertTrue(one.isdisjoint(two))
        self.assertEqual(set.union(*networks),pipes)

    def test_new_machines_are_covered_and_new_wires_reach(self):
        poles=[e for e in self.entities.values() if e['name'] in ('small-electric-pole','medium-electric-pole','substation')]
        machine_names=('electric-mining-drill','pumpjack','chemical-plant','oil-refinery','electric-furnace','inserter')
        sizes={'oil-refinery':2.5,'inserter':.5}
        radius={'small-electric-pole':2.5,'medium-electric-pole':3.5,'substation':9}
        for n,e in self.entities.items():
            if n<=1213 or e['name'] not in machine_names:continue
            p=e['position']; size=sizes.get(e['name'],1.5)
            self.assertTrue(any(abs(p['x']-q['position']['x'])<radius[q['name']]+size and
                                abs(p['y']-q['position']['y'])<radius[q['name']]+size
                                for q in poles),(n,e['name']))
        for a,c,b,d in self.data['blueprint']['wires']:
            if max(a,b)<=1213 or c!=5 or d!=5: continue
            p=self.entities[a]['position']; q=self.entities[b]['position']
            self.assertLessEqual(math.hypot(p['x']-q['x'],p['y']-q['y']),9,(a,b))
