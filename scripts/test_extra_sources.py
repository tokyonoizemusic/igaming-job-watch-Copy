import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from sources_extra import Links, collect_rss, collect_careers, candidate, CAREER_PAGES
from unittest.mock import patch

class ExtraSourceTests(unittest.TestCase):
    def test_linkedin_rss_canonical_and_invalid(self):
        xml='''<rss><channel><item><title>Senior Game Producer - REEVO | LinkedIn</title><link>https://www.linkedin.com/jobs/view/4470861920/?trackingId=test</link></item><item><title>Unrelated ad</title><link>https://www.linkedin.com/jobs/view/22222/</link></item></channel></rss>'''
        rows=collect_rss(xml,'test')
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['url'],'https://www.linkedin.com/jobs/view/4470861920/')
        self.assertFalse(rows[0]['verified'])
        self.assertEqual(rows[0]['sourceKind'],'indexed-search')
    def test_google_alert_atom(self):
        xml='''<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Senior Sound Designer - Enjoy Gaming | LinkedIn</title><link href="https://www.linkedin.com/jobs/view/12345678/" /></entry></feed>'''
        rows=collect_rss(xml,'Google Alerts')
        self.assertEqual(len(rows),1)
    def test_career_link_on_official_site(self):
        body='''<html><body><a href="/jobs/1234-senior-game-producer">Senior Game Producer</a><a href="/jobs/222-senior-engineer">Senior backend engineer</a></body></html>'''
        with patch('sources_extra.fetch_text',lambda url:(body,url,'text/html')):
            rows=collect_careers('Push Gaming','https://pushgaming.teamtailor.com/jobs')
        self.assertEqual(len(rows),1)
        self.assertIn('/jobs/1234-senior-game-producer',rows[0]['url'])
    def test_structured_job_posting(self):
        body='''<script type="application/ld+json">{"@context":"https://schema.org","@type":"JobPosting","title":"Product Owner","url":"https://example.com/jobs/po","jobLocation":{"address":{"addressLocality":"Bucharest","addressCountry":"Romania"}}}</script>'''
        with patch('sources_extra.fetch_text',lambda url:(body,url,'text/html')):
            rows=collect_careers('Example Studio','https://example.com/careers/')
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['region'],'romania')
    def test_company_count(self):
        self.assertGreaterEqual(len(CAREER_PAGES),25)
if __name__=='__main__':unittest.main()
