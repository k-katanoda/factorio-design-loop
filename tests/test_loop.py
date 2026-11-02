import json,sys, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
from loop import load, inspect, encode, decode, patch_data, diff_data, check_geometry
import copy

BASE=load(HERE/'designs'/'nuclear_baseline.txt')
FIXED=load(HERE/'designs'/'nuclear_candidate_v1.txt')

class LoopRegressionTests(unittest.TestCase):
    def test_blueprint_roundtrip(self):
        self.assertEqual(decode(encode(BASE)),BASE)
    def test_original_has_disconnected_water(self):
        r=inspect(BASE)
        self.assertEqual(r['water']['reachable'],0)
        self.assertEqual(r['water']['inputs'],48)
        self.assertEqual(r['steam']['reachable'],84)
        self.assertEqual(r['status'],'FAIL')
    def test_candidate_restores_all_water_connections(self):
        r=inspect(FIXED)
        self.assertEqual(r['status'],'PASS_STATIC_LIMITED')
        self.assertEqual(r['water']['reachable'],48)
        self.assertEqual(r['steam']['reachable'],84)
        self.assertEqual(r['underground_unpaired'],[])
        self.assertEqual(r['geometry_errors'],[])
    def test_new_break_detected(self):
        candidate=copy.deepcopy(FIXED)
        es=candidate['blueprint']['entities']
        es.remove(next(e for e in es if e['entity_number']==777))
        r=inspect(candidate)
        self.assertEqual(r['status'],'FAIL')
        self.assertEqual(r['water']['reachable'],0)
    def test_precondition_refuses_wrong_target(self):
        patch={'operations':[{'op':'remove','id':622,'expect_name':'nuclear-reactor'}]}
        with self.assertRaisesRegex(ValueError,'Precondition'):
            patch_data(copy.deepcopy(BASE),patch)
    def test_diff_has_only_expected_changes(self):
        r=diff_data(BASE,FIXED)
        self.assertEqual([e['entity_number'] for e in r['added']],[777])
        self.assertEqual([e['entity_number'] for e in r['removed']],[620])
        self.assertEqual([e['before']['entity_number'] for e in r['updated']],[622])
    def test_invalid_position_detected(self):
        b=copy.deepcopy(FIXED)
        e=next(e for e in b['blueprint']['entities'] if e['name']=='heat-exchanger')
        e['position']['y']+=.5
        r=inspect(b)
        self.assertEqual(r['status'],'FAIL')
        self.assertTrue(r['geometry_errors'])
    def test_overlap_detected(self):
        b=copy.deepcopy(FIXED)
        e=next(e for e in b['blueprint']['entities'] if e['name']=='pipe')
        b['blueprint']['entities'].append({'entity_number':9999,'name':'pipe','position':e['position']})
        r=inspect(b)
        self.assertEqual(r['status'],'FAIL')
        self.assertTrue(any('Overlapping' in err for err in r['geometry_errors']))

if __name__=='__main__':unittest.main()

class ReleaseIntegrityTests(unittest.TestCase):
    def test_selected_revision_matches_patch(self):
        from verify_release import check
        self.assertEqual(check(), 'r001')

    def test_all_steam_exchanger_outputs_reach_turbines(self):
        from loop import entities, build_graph, walk
        es=entities(FIXED)
        adj,*_=build_graph(es)
        terminals=[(e['entity_number'],'steam') for e in es if e['name']=='heat-exchanger']
        targets=[(e['entity_number'],'steam') for e in es if e['name']=='steam-turbine']
        self.assertEqual(sum(t in walk(adj,targets) for t in terminals),len(terminals))
