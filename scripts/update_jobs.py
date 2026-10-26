#!/usr/bin/env python3
"""Daily, best-effort collection from publicly exposed employer job boards.

No LinkedIn scraping, no protected endpoints, no invented vacancy verification.
The output is a snapshot of postings returned by each successful ATS API.
"""
import datetime as dt
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from sources_extra import CAREER_PAGES, collect_careers, linkedin_rss_sources, fetch_text, collect_rss
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'public' / 'data' / 'jobs.json'
TODAY = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')
STAMP = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
HEADERS = {'User-Agent': 'European-iGaming-Job-Watch/1.0 (public job board refresh; non-commercial)', 'Accept': 'application/json'}
SOURCES = [
    {'name': 'Oddin.gg', 'type': 'lever', 'token': 'oddin'},
    {'name': 'Betsson Group', 'type': 'greenhouse', 'token': 'betsson'},
    {'name': 'Playtech', 'type': 'smartrecruiters', 'token': 'Playtech'},
    # Recruitee is moving towards authenticated API access; unsuccessful scans are flagged.
    {'name': 'Enjoy Gaming', 'type': 'recruitee', 'token': 'enjoygaming'},
]
ROLE = re.compile(r'\b(game\s*(producer|director|designer|product\s*(owner|manager))|(?:senior\s+)?(?:casino|slot|iGaming)\s*(?:game\s*)?(?:producer|product\s*(?:owner|manager)|designer)|product\s*owner|product\s*manager|sound\s*designer|audio\s*(?:lead|director|producer|designer|manager)|composer|music\s*composer|technical\s*sound\s*designer)\b', re.I)
EXCLUDE = re.compile(r'\b(trader|sales|marketing|hr|human resources|recruitment|talent acquisition|security|customer support|content marketing|copywriter|speech synthesis|text.to.speech)\b', re.I)
EUROPE = re.compile(r'\b(europe|eu\b|remote|worldwide|global|romania|bucharest|cluj|malta|cyprus|gibraltar|sweden|finland|norway|denmark|poland|warsaw|krakow|estonia|latvia|lithuania|bulgaria|sofia|serbia|belgrade|slovakia|bratislava|czech|prague|germany|berlin|austria|vienna|hungary|budapest|portugal|spain|madrid|barcelona|italy|france|paris|netherlands|amsterdam|ireland|dublin|united kingdom|uk\b|london|georgia|tbilisi|isle of man|belgium|greece|athens|ukraine|kyiv)\b', re.I)
NOT_EUROPE = re.compile(r'\b(united states|usa|canada|mexico|brazil|peru|lima|colombia|india|philippines|pakistan|south africa|australia|argentina|singapore|dubai|uae)\b', re.I)


def get_json(url):
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=18) as response:
        return json.load(response)


def clean(text):
    return re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]*>', ' ', str(text or '')))).strip()


def workplace(location, explicit=''):
    combined = (location + ' ' + explicit).lower()
    if 'hybrid' in combined:
        return 'hybrid'
    if 'remote' in combined or 'work from anywhere' in combined:
        return 'remote'
    if 'on-site' in combined or 'onsite' in combined or 'on site' in combined:
        return 'onsite'
    return 'unknown'


def region(location, mode):
    if re.search(r'\bromania|bucharest|cluj|timisoara\b', location, re.I):
        return 'romania'
    if NOT_EUROPE.search(location) and not EUROPE.search(location):
        return 'restricted'
    if EUROPE.search(location):
        return 'eu'
    # Remote job that merely says 'Remote' does not prove Romania is eligible.
    return 'unclear'


def acceptable(title, location):
    if not ROLE.search(title) or EXCLUDE.search(title):
        return False
    if NOT_EUROPE.search(location) and not EUROPE.search(location):
        return False
    return True


def make_job(source, external_id, title, location, url, posted='', arrangement='', description=''):
    if not acceptable(title, location):
        return None
    if not str(url).startswith('https://'):
        return None
    mode = workplace(location, arrangement)
    area = region(location, mode)
    if 'sound' in title.lower() or 'audio' in title.lower() or 'composer' in title.lower():
        category = 'audio'
    else:
        category = 'production'
    if area == 'romania':
        eligibility = 'Romania location advertised. Confirm residence, contract and any onsite requirements.'
    elif area == 'eu':
        eligibility = 'European location or remote indicated. Cross-border employment from Romania is NOT confirmed.'
    elif area == 'restricted':
        eligibility = 'Location may exclude Romanian applicants. Check employer.'
    else:
        eligibility = 'Remote or location conditions unclear; confirm eligibility to work from Romania.'
    return dict(
        id=f'feed-{source["type"]}-{source["token"].lower()}-{external_id}',
        company=source['name'], title=clean(title), category=category,
        location=clean(location) or 'Unspecified', mode=mode, region=area,
        eligibility=eligibility, fit='Strong' if (re.search(r'game\s*producer|sound\s*designer|product\s*owner', title, re.I)) else 'Relevant',
        url=url, notes='Automatic discovery from published employer job board. Check full requirements and country eligibility.',
        checked=TODAY, verified=False, liveFeed=True, sourceKind='automatic', source=source['type'],
        datePosted=str(posted or '')[:10], status='not-started', saved=False, added=TODAY,
    )


def fetch_lever(s):
    url=f'https://api.lever.co/v0/postings/{s["token"]}?mode=json&limit=100'
    data=get_json(url)
    if not isinstance(data, list):
        raise ValueError('Unexpected Lever response')
    output=[]
    for j in data:
        cats=j.get('categories') or {}
        loc=cats.get('location') or j.get('workplaceType') or ''
        arrangement=(j.get('workplaceType') or '')
        if arrangement and arrangement.lower() not in loc.lower():
            loc=f'{loc} · {arrangement}'
        posted=j.get('createdAt','')
        if isinstance(posted, (int,float)):
            posted=dt.datetime.fromtimestamp(posted/1000,dt.timezone.utc).strftime('%Y-%m-%d')
        job=make_job(s,j.get('id'),j.get('text',''),loc,j.get('hostedUrl',''),posted,arrangement)
        if job:output.append(job)
    return output


def fetch_greenhouse(s):
    url=f'https://boards-api.greenhouse.io/v1/boards/{s["token"]}/jobs'
    data=get_json(url)
    if not isinstance(data.get('jobs'), list):
        raise ValueError('Unexpected Greenhouse response')
    output=[]
    for j in data['jobs']:
        loc=(j.get('location') or {}).get('name','')
        job=make_job(s,j.get('id'),j.get('title',''),loc,j.get('absolute_url',''),j.get('first_published') or j.get('updated_at',''))
        if job:output.append(job)
    return output


def fetch_smartrecruiters(s):
    url=f'https://api.smartrecruiters.com/v1/companies/{s["token"]}/postings?limit=100'
    data=get_json(url)
    if not isinstance(data.get('content'),list):
        raise ValueError('Unexpected SmartRecruiters response')
    output=[]
    for j in data['content']:
        loc_obj=j.get('location') or {}
        loc=', '.join(str(loc_obj[k]) for k in ('city','country') if loc_obj.get(k))
        if loc_obj.get('remote'): loc+=' · Remote'
        url=j.get('ref') or j.get('applyUrl') or ''
        # ref is an API detail URL, not an application page.
        if '/v1/' in url and 'api.smartrecruiters.com' in url: url=''
        if not url:
            url=f'https://jobs.smartrecruiters.com/{s["token"]}/{j.get("id","")}'
        job=make_job(s,j.get('id'),j.get('name',''),loc,url,j.get('releasedDate') or j.get('postingDate',''))
        if job:output.append(job)
    return output


def fetch_recruitee(s):
    url=f'https://{s["token"]}.recruitee.com/api/offers/'
    data=get_json(url)
    if not isinstance(data.get('offers'), list):
        raise ValueError('Unexpected Recruitee response')
    output=[]
    for j in data['offers']:
        loc=(j.get('location') or j.get('city') or '')
        if isinstance(loc,dict):loc=', '.join(str(x) for x in (loc.get('city'),loc.get('country')) if x)
        mode_info=j.get('remote')
        if mode_info:loc+=' · Remote'
        url=j.get('careers_url') or j.get('url') or j.get('offer_url') or ''
        if not url and j.get('slug'): url=f'https://{s["token"]}.recruitee.com/o/{j["slug"]}'
        job=make_job(s,j.get('id'),j.get('title',''),loc,url,j.get('published_at') or j.get('created_at',''))
        if job:output.append(job)
    return output

FETCH={'lever':fetch_lever,'greenhouse':fetch_greenhouse,'smartrecruiters':fetch_smartrecruiters,'recruitee':fetch_recruitee}


def main():
    previous={}
    if OUT.exists():
        try: previous=json.loads(OUT.read_text(encoding='utf-8'))
        except Exception:pass
    prev_by_id={j['id']:j for j in previous.get('jobs',[]) if isinstance(j,dict) and j.get('id')}
    jobs=[];status=[]
    for source in SOURCES:
        try:
            entries=FETCH[source['type']](source)
            for j in entries:
                old=prev_by_id.get(j['id']) or {}
                j['firstSeen']=old.get('firstSeen') or TODAY
                j['added']=j['firstSeen']
                jobs.append(j)
            status.append({'company':source['name'],'type':source['type'],'ok':True,'matches':len(entries)})
        except Exception as exc:
            print(f'WARNING {source["name"]}: {exc}', file=sys.stderr)
            # Keep previous results only as stale, and distinguish them from currently confirmed.
            prior=[dict(j) for j in prev_by_id.values() if j.get('source')==source['type'] and j.get('company')==source['name']]
            for j in prior:
                j['liveFeed']=False
                j['notes']='Source refresh failed; this listing is from an older snapshot. Verify before applying.'
                jobs.append(j)
            status.append({'company':source['name'],'type':source['type'],'ok':False,'matches':0,'error':'Source temporarily unavailable'})
        time.sleep(0.1)
    # Additional public employer careers pages (no credentials, no LinkedIn HTML scraping).
    # Some pages are JS-only; an empty extraction is NOT an absence-of-vacancies claim.
    def check_career(entry):
        company,url=entry
        try:return (company, collect_careers(company,url), None)
        except Exception as exc:return (company,[],str(exc))
    print(f'Checking {len(CAREER_PAGES)} extra public career pages …')
    with ThreadPoolExecutor(max_workers=6) as pool:
        for future in as_completed([pool.submit(check_career, entry) for entry in CAREER_PAGES]):
            company,entries,error=future.result()
            status.append({'company':company,'type':'career-page','ok':not bool(error),'matches':len(entries),
                           'coverage':'HTML/job structured data where publicly available','error':'Page inaccessible or unsupported' if error else ''})
            if error:print(f'WARNING careers page {company}: {error[:130]}',file=sys.stderr)
            for j in entries:
                old=prev_by_id.get(j['id']) or {}
                j['firstSeen']=old.get('firstSeen') or TODAY
                j['added']=old.get('added') or j['firstSeen']
                jobs.append(j)
    # Best-effort search-engine index discovery. NEVER call linkedin.com itself.
    # No search source being blocked may be represented as an absence of jobs.
    for name,url in linkedin_rss_sources():
        try:
            txt,_,_=fetch_text(url,timeout=12)
            entries=collect_rss(txt,name)
            for j in entries:
                old=prev_by_id.get(j['id']) or {}
                j['firstSeen']=old.get('firstSeen') or TODAY
                j['added']=old.get('added') or j['firstSeen']
                jobs.append(j)
            status.append({'company':name,'type':'linkedin-indexed-rss','ok':True,'matches':len(entries),
                           'coverage':'Search-index lead discovery, not direct LinkedIn vacancy verification'})
        except Exception as exc:
            status.append({'company':name,'type':'linkedin-indexed-rss','ok':False,'matches':0,
                           'error':'RSS unavailable; LinkedIn search shortcuts remain available'})
            print(f'WARNING {name}: {exc}',file=sys.stderr)
        time.sleep(0.15)
    unique={j['id']:j for j in jobs}
    output={'checked_at':STAMP,'timezone':'Europe/Bucharest','sources':status,'watchlist_count':len(SOURCES)+len(CAREER_PAGES),'linkedin_discovery':'Best-effort RSS search index; not direct LinkedIn access or vacancy verification','jobs':sorted(unique.values(),key=lambda j:(j.get('firstSeen',''),j.get('company','')),reverse=True)}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n', encoding='utf-8')
    print('Total',len(unique),'matching positions; sources',status)
    # A failed provider is shown on the site, without claiming a successful full refresh.

if __name__ == '__main__':main()
