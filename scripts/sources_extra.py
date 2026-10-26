"""Small-volume public careers-page discovery and best-effort LinkedIn-indexed RSS.

No login bypass, browser automation, LinkedIn scraping, or unverified 'open' assertions.
Static career pages can have no machine-readable jobs; these are monitored but
not treated as comprehensive sources. RSS results are leads, NOT verified jobs.
"""
import datetime as dt
import hashlib
import html
from html.parser import HTMLParser
import json
import os
import re
from urllib.parse import urljoin, urlparse, urlencode, parse_qs, unquote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

# These company pages are periodically CHECKED; presence alone does not imply a
# machine-readable feed or that a job was found. Most links are user-supplied
# and match the dashboard's existing studio directory.
CAREER_PAGES = [
 ('Push Gaming', 'https://pushgaming.teamtailor.com/jobs'),
 ('Relax Gaming', 'https://careers.relax-gaming.com/jobs'),
 ('Hacksaw Gaming', 'https://www.hacksawgaming.com/careers/all'),
 ('BGaming', 'https://bgaming.com/careers'),
 ('Playson', 'https://playson.com/career'),
 ('Games Global', 'https://careers.gamesglobal.com/jobs'),
 ('RubyPlay', 'https://careers.rubyplay.com/'),
 ('Booming Games', 'https://booming-games.jobs.personio.com/?language=en'),
 ('Greentube', 'https://careers.greentube.com/'),
 ('Bragg Gaming', 'https://bragg.group/careers/'),
 ('Stakelogic', 'https://stakelogic.com/en/careers/'),
 ('Thunderkick', 'https://www.thunderkick.com/career/'),
 ('Wazdan', 'https://wazdan.com/career'),
 ('Yggdrasil', 'https://yggdrasilgaming.com/careers'),
 ("Play'n GO", 'https://www.playngo.com/careers-positions'),
 ('ELK Studios', 'https://www.elk-studios.com/career/'),
 ('Quickspin', 'https://quickspin.com/career/'),
 ('Blueprint Gaming', 'https://blueprintgaming.com/careers/'),
 ('EveryMatrix', 'https://everymatrix.com/'),
 ('LeoVegas', 'https://www.leovegasgroup.com/careers/open-positions/'),
 ('Entain', 'https://entaincareers.com/job-search/'),
 ('Kaizen Gaming', 'https://careers.kaizengaming.com/'),
 ('CLAWBUSTER', 'https://clawbuster.com/vacancies/'),
 ('Gamdom', 'https://www.gamdomcareers.com/jobs'),
 ('REEVO', 'https://reevotech.com/careers/'),
 ('Kendoo', 'https://kendoo.peopleforce.io/careers'),
 ('ARRISE', 'https://arrise.com/careers/'),
]
HEADER = {'User-Agent':'Mozilla/5.0 (compatible; iGaming-Job-Watch/2.0; +https://github.com/tokyonoizemusic/igaming-job-watch-Copy)', 'Accept':'text/html, application/rss+xml, application/xml'}
ROLE = re.compile(r'(?:\b(?:head|lead|senior|principal|executive|studio|casino|slot|game|audio|music|product|project|creative|technical|iGaming|compos)\b.*\b(?:producer|owner|designer|director|manager|lead|composer|production)\b|\b(?:sound designer|game designer|game producer|product owner|product manager|audio lead|studio director)\b)',re.I)
BAD = re.compile(r'\b(?:marketing|recruitment|copywriter|content creator|player support|sales manager|trader|customer support|security engineer|UI designer|backend developer|frontend developer|developer relations)\b',re.I)
PATH = re.compile(r'/(?:jobs/[0-9][^/]*|job/[a-z0-9][^/]*|careers/v/[0-9][^/]*|o/[a-z][a-z0-9-]*|vacancies/[a-z0-9-]+(?:\.html)?|jobs/\d+|position/[a-z0-9-]+|positions/[a-z0-9-]+|career/[a-z0-9-]+)$',re.I)


def fetch_text(url,timeout=13):
    req=Request(url,headers=HEADER)
    with urlopen(req,timeout=timeout) as resp:
        ty=resp.headers.get('Content-Type','')
        raw=resp.read(1_200_000)
        return raw.decode('utf-8',errors='replace'), resp.geturl(),ty

class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.current=None;self.parts=[];self.scripts=[];self.script_type=None;self.script_parts=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='a':self.current=attrs.get('href');self.parts=[]
        if tag=='script' and attrs.get('type')=='application/ld+json':self.script_type='ld';self.script_parts=[]
    def handle_data(self,data):
        if self.current is not None:self.parts.append(data)
        if self.script_type=='ld':self.script_parts.append(data)
    def handle_endtag(self,tag):
        if tag=='a' and self.current is not None:
            self.links.append((self.current, re.sub(r'\s+',' ',' '.join(self.parts)).strip()))
            self.current=None;self.parts=[]
        if tag=='script' and self.script_type=='ld':
            self.scripts.append(''.join(self.script_parts));self.script_type=None;self.script_parts=[]


def candidate(name,url,title,posted='',location='Location not specified'):
    if not ROLE.search(title) or BAD.search(title) or len(title)>165:return None
    if not url.startswith('https://'):return None
    ident=hashlib.sha1((name+'|'+url).encode()).hexdigest()[:16]
    category='audio' if re.search(r'audio|sound|music|composer',title,re.I) else 'production'
    region='romania' if re.search(r'romania|bucharest|cluj',location,re.I) else 'eu' if re.search(r'EU\b|Europe|Malta|UK|Poland|Gibraltar|Cyprus',location,re.I) else 'unclear'
    work='remote' if re.search(r'remote',location,re.I) else 'hybrid' if re.search(r'hybrid',location,re.I) else 'unknown'
    return {'id':'careers-'+ident,'company':name,'title':title,'category':category,'location':location,'mode':work,
      'region':region,'eligibility':'Location and Romania eligibility not verified; open employer page and confirm.',
      'fit':'Unrated','url':url,'notes':'Found on public careers page; title/link extracted automatically. Posting and eligibility NOT independently verified.',
      'checked':dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d'),'verified':False,'liveFeed':True,
      'sourceKind':'careers-discovery','source':'company-careers','datePosted':str(posted or '')[:10],
      'status':'not-started','saved':False}


def collect_careers(name,base):
    body,final,ty=fetch_text(base)
    p=Links();p.feed(body)
    found=[];seen=set()
    for script in p.scripts:
      try: obj=json.loads(script)
      except Exception:continue
      def expand(x):
        if isinstance(x,list):
          for v in x:yield from expand(v)
        if isinstance(x,dict):
          if x.get('@type') == 'JobPosting' or (isinstance(x.get('@type'),list) and 'JobPosting' in x['@type']):
            yield x
          for v in x.values():
            if isinstance(v,(dict,list)):yield from expand(v)
      for j in expand(obj):
        title=html.unescape(str(j.get('title') or ''))
        link=urljoin(final,str(j.get('url') or base))
        locobj=j.get('jobLocation') or {}; loc='Location not specified'
        if isinstance(locobj,dict):
          addr=locobj.get('address') or {}
          if isinstance(addr,dict):loc=', '.join(str(addr.get(k)) for k in ('addressLocality','addressCountry') if addr.get(k)) or loc
        job=candidate(name,link,title,j.get('datePosted',''),loc)
        if job and job['url'] not in seen:seen.add(job['url']);found.append(job)
    for href,title in p.links:
      link=urljoin(final,href.split('#')[0]);path=urlparse(link).path.rstrip('/')
      if not PATH.search(path) or not ROLE.search(title):continue
      job=candidate(name,link,title)
      if job and link not in seen:found.append(job);seen.add(link)
    return found


def normalize_li_link(link):
    from urllib.parse import urlparse,parse_qs
    p=urlparse(link)
    if p.hostname not in ('www.linkedin.com','linkedin.com'):return None
    m=re.search(r'/jobs/view/(\d+)',p.path)
    return 'https://www.linkedin.com/jobs/view/'+m.group(1)+'/' if m else None


def collect_rss(text,source_label):
    """Accept RSS items or Atom entries with direct LinkedIn vacancy links only."""
    doc=ET.fromstring(text)
    nodes=[]
    for item in doc.findall('.//item'):
        nodes.append((item.findtext('link') or '',item.findtext('title') or ''))
    atom='{http://www.w3.org/2005/Atom}'
    for entry in doc.findall('.//'+atom+'entry'):
        links=entry.findall(atom+'link')
        url=next((link.get('href') for link in links if link.get('href')),'')
        nodes.append((url,entry.findtext(atom+'title') or ''))
    found=[];seen=set()
    for raw_link,raw_title in nodes:
      raw_link=raw_link.strip()
      # Google Alerts may wrap a public LinkedIn URL with an explicit q/url param.
      p=urlparse(raw_link)
      if p.hostname in ('www.google.com','google.com') and p.path=='/url':
          params=parse_qs(p.query)
          raw_link=(params.get('url') or params.get('q') or [''])[0]
      link=normalize_li_link(raw_link)
      if not link or link in seen:continue
      title=html.unescape(re.sub('<[^>]+>','',raw_title)).strip()
      title=re.sub(r'\s*[|–-]\s*LinkedIn\s*$','',title,flags=re.I)
      if not ROLE.search(title) or BAD.search(title):continue
      seen.add(link)
      m=re.split(r'\s+[|–-]\s+',title)
      company='LinkedIn indexed (employer unconfirmed)';display=title
      if len(m)>1:
        display=m[0][:120]
        if len(m[1])<70:company=m[1]
      ident=re.search(r'/view/(\d+)',link).group(1)
      found.append({'id':'linkedin-index-'+ident,'company':company,'title':display,'category':'audio' if re.search(r'audio|sound|music|composer',display,re.I) else 'production',
        'location':'Location unverified · LinkedIn indexed','mode':'unknown','region':'unclear',
        'eligibility':'Unknown; search-index result only. Check LinkedIn/official employer listing.',
        'fit':'Unrated','url':link,'notes':'Unverified LinkedIn-indexed discovery via '+source_label+'. Search index can be stale; confirm role, employer, and location. NOT a direct LinkedIn API feed.',
        'checked':dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d'),'verified':False,'liveFeed':True,
        'sourceKind':'indexed-search','source':source_label,'datePosted':'','status':'not-started','saved':False})
    return found

def linkedin_rss_sources():
    # Bing public RSS is experimental/best effort; small daily query volume.
    queries=[
      'site:linkedin.com/jobs/view/ "game producer" "remote" Europe',
      'site:linkedin.com/jobs/view/ "product owner" "iGaming" Romania',
      'site:linkedin.com/jobs/view/ "sound designer" "casino" Europe',
      'site:linkedin.com/jobs/view/ "game designer" "slots" "European Union"',
    ]
    for i,query in enumerate(queries,1):
        yield (f'LinkedIn indexed search {i}', 'https://www.bing.com/search?'+urlencode({'q':query,'format':'rss'}))
    # Optional Google Alerts RSS urls are private configuration: supply via
    # GitHub Actions secret JOB_ALERT_RSS_URLS, separated by newlines.
    urls=os.environ.get('JOB_ALERT_RSS_URLS','').splitlines()
    for i,url in enumerate(urls,1):
        url=url.strip()
        if url.startswith('https://www.google.com/alerts/feeds/'):
            yield (f'LinkedIn Google Alerts {i}',url)
