import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import update_jobs as u

class FeedTests(unittest.TestCase):
    def test_slot_role_match(self):
        self.assertTrue(u.acceptable('Senior Game Producer (RNG & Instant Win Games)','Prague · Remote'))
        self.assertTrue(u.acceptable('Senior Sound Designer (Slots)','Bratislava'))
        self.assertTrue(u.acceptable('Product Owner','Remote Europe'))
    def test_excludes_nonroles_and_outside(self):
        self.assertFalse(u.acceptable('Customer Support Agent','Malta'))
        self.assertFalse(u.acceptable('Game Producer','Lima, Peru'))
        self.assertFalse(u.acceptable('Marketing Product Manager','Remote Europe'))
    def test_does_not_overclaim_remote_eligibility(self):
        job=u.make_job({'type':'lever','token':'oddin','name':'Oddin.gg'},'id','Senior Game Producer','Prague · Remote','https://jobs.lever.co/oddin/id')
        self.assertEqual(job['mode'],'remote')
        self.assertIn('NOT confirmed',job['eligibility'])
        self.assertFalse(job['verified'])
    def test_recruitee_sample(self):
        original=u.get_json
        try:
            u.get_json=lambda _: {'offers':[{'id':7,'title':'Senior Sound Designer (slots)','location':{'city':'Bratislava','country':'Slovakia'},'remote':True,'slug':'senior-sound-designer-slots'}]}
            jobs=u.fetch_recruitee({'type':'recruitee','token':'enjoygaming','name':'Enjoy Gaming'})
            self.assertEqual(len(jobs),1)
            self.assertEqual(jobs[0]['category'],'audio')
        finally:u.get_json=original
    def test_lever_sample(self):
        original=u.get_json
        try:
            u.get_json=lambda _: [{'id':'123','text':'Senior Game Producer','hostedUrl':'https://jobs.lever.co/oddin/123','categories':{'location':'Prague'},'workplaceType':'remote','createdAt':1790000000000}]
            jobs=u.fetch_lever({'type':'lever','token':'oddin','name':'Oddin.gg'})
            self.assertEqual(len(jobs),1)
            self.assertEqual(jobs[0]['mode'],'remote')
        finally:u.get_json=original

if __name__=='__main__':unittest.main()
