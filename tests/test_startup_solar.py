import math
import unittest
import loop
import integrate_startup_solar as solar

class StartupSolarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=solar.build();cls.bp=cls.data['blueprint'];cls.entities={e['entity_number']:e for e in cls.bp['entities']}
        cls.old=loop.load('designs/nuclear_mining_provisional.txt')['blueprint'];cls.old_max=max(e['entity_number'] for e in cls.old['entities'])
        cls.new=[e for n,e in cls.entities.items() if n>cls.old_max]

    def test_reproducible_and_capacity(self):
        self.assertEqual(self.data,loop.load('designs/nuclear_solar_startup_candidate.txt'))
        self.assertEqual(sum(e['name']=='solar-panel' for e in self.new),200)
        self.assertEqual(sum(e['name']=='accumulator' for e in self.new),1)
        self.assertEqual(sum(e['name']=='substation' for e in self.new),6)
        bound=sum([17*(350+350/30),375+12.5,2*(180+6),2*(210+7),420+14,
                   4*(90+3),90+3,41*(59.3+.5),4*(169+1),8*(21.4+.4),11*(15.1+.4),16*5,4])
        self.assertLess(bound,200*60)
        # Extra generation must be available to charge the accumulator at peak load.
        self.assertGreater(200*60-bound,0)

    def test_wire_network_reaches_existing_substation(self):
        substations={e['entity_number']:e for e in self.new if e['name']=='substation'}
        adjacency={n:set() for n in substations};adjacency[1131]=set()
        for a,c,b,d in self.bp.get('wires',[]):
            if c==d==5 and a in adjacency and b in adjacency:
                p=self.entities[a]['position'];q=self.entities[b]['position']
                self.assertLessEqual(math.hypot(p['x']-q['x'],p['y']-q['y']),18)
                adjacency[a].add(b);adjacency[b].add(a)
        seen={1131};stack=[1131]
        while stack:
            for b in adjacency[stack.pop()]-seen: seen.add(b);stack.append(b)
        self.assertEqual(seen,set(adjacency))
        for e in self.new:
            if e['name'] not in ('solar-panel','accumulator'):continue
            p=e['position'];half=1.5 if e['name']=='solar-panel' else 1
            self.assertTrue(any(abs(p['x']-s['position']['x']) < 9+half and abs(p['y']-s['position']['y']) < 9+half for s in substations.values()),e)

    def test_new_components_do_not_overlap(self):
        sizes={'nuclear-reactor':(5,5),'heat-exchanger':(3,2),'steam-turbine':(3,5),
               'storage-tank':(3,3),'substation':(2,2),'centrifuge':(3,3),'solar-panel':(3,3),'accumulator':(2,2),
               'assembling-machine-3':(3,3),'electric-furnace':(3,3),'electric-mining-drill':(3,3),
               'chemical-plant':(3,3),'pumpjack':(3,3),'oil-refinery':(5,5),
               'decider-combinator':(1,2),'splitter':(2,1),'fast-splitter':(2,1)}
        def rect(e):
            w,h=sizes.get(e['name'],(1,1))
            if e['name'] in ('heat-exchanger','steam-turbine','decider-combinator','splitter','fast-splitter') and e.get('direction',0)%8==4:w,h=h,w
            p=e['position'];return p['x']-w/2,p['y']-h/2,p['x']+w/2,p['y']+h/2
        def collide(a,b):return a[0]<b[2]-1e-9 and b[0]<a[2]-1e-9 and a[1]<b[3]-1e-9 and b[1]<a[3]-1e-9
        for e in self.new:
            for f in self.entities.values():
                if f['entity_number']<e['entity_number']:
                    self.assertFalse(collide(rect(e),rect(f)),(e['entity_number'],f['entity_number']))

    def test_electric_consumers_have_coverage_on_connected_network(self):
        pole_names={'small-electric-pole','medium-electric-pole','substation'}
        poles={n:e for n,e in self.entities.items() if e['name'] in pole_names}
        rad={'small-electric-pole':2.5,'medium-electric-pole':3.5,'substation':9}
        adj={n:set() for n in poles}
        for a,c,b,d in self.bp.get('wires',[]):
            if c==d==5 and a in poles and b in poles:adj[a].add(b);adj[b].add(a)
        seen={1131};stack=[1131]
        while stack:
            for n in adj[stack.pop()]-seen:seen.add(n);stack.append(n)
        self.assertEqual(seen,set(poles))
        sizes={'centrifuge':(1.5,1.5),'chemical-plant':(1.5,1.5),'assembling-machine-3':(1.5,1.5),
               'oil-refinery':(2.5,2.5),'electric-furnace':(1.5,1.5),'electric-mining-drill':(1.5,1.5),
               'pumpjack':(1.5,1.5),'inserter':(.5,.5),'fast-inserter':(.5,.5),'bulk-inserter':(.5,.5),
               'long-handed-inserter':(.5,.5),'small-lamp':(.5,.5),'decider-combinator':(.5,1)}
        for e in self.entities.values():
            if e['name'] not in sizes:continue
            w,h=sizes[e['name']]
            if e['name']=='decider-combinator' and e.get('direction',0)%8==4:w,h=h,w
            p=e['position']
            self.assertTrue(any(abs(p['x']-q['position']['x'])<w+rad[q['name']] and
                                abs(p['y']-q['position']['y'])<h+rad[q['name']]
                                for q in poles.values()),(e['entity_number'],e['name']))
