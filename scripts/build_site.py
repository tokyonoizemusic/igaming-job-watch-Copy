from pathlib import Path
src=Path('/mnt/data/European_iGaming_Job_Watch_v3.html').read_text(encoding='utf-8')
dst=Path(__file__).resolve().parents[1]/'public'/'index.html'
src=src.replace('<title>European iGaming Job Watch V3</title>','<title>European iGaming Job Watch — Daily Live Dashboard</title>')
src=src.replace('<h1>European iGaming <span style="color:var(--accent)">Job Watch</span></h1>','<h1>European iGaming <span style="color:var(--accent)">Job Watch</span> <span style="color:#72eab6;font-size:14px;letter-spacing:0;white-space:nowrap">● Daily Live</span></h1>')
src=src.replace('Your personal dashboard for slot & casino Game Producer, Product Owner, Sound Designer, and Audio Lead opportunities. Track applications locally and open live job searches in a new tab.', 'CV-targeted slots, crash games & casino roles. Daily employer-feed updates when hosted, 30+ external search shortcuts, and private application tracking in your browser.')
src=src.replace('This HTML dashboard does <strong>not</strong> retrieve jobs or synchronize with your ChatGPT weekly automation. The entries below are leads identified in an earlier search, <strong>not freshly reverified open vacancies</strong>. Use “Open vacancy” to check if a posting is still active, and use the live-search links for new results. Your changes stay in this browser only. The new multi-source search opens current results <strong>on external sites</strong>; it cannot fetch them automatically from LinkedIn or other protected platforms.', 'The hosted version downloads its daily job-feed snapshot from publicly accessible employer recruitment systems. The existing curated leads are historical and <strong>not guaranteed to remain open</strong>. The separate daily ChatGPT job-watch report does <strong>not</strong> automatically write to this website. LinkedIn and other external job boards remain search links, not scraped feeds. Application statuses/notes remain private in <strong>this browser only</strong>.')
anchor='<section class="discovery" id="discovery" aria-label="Multi-source job discovery">'
banner='''<section class="panel" style="margin:17px 0 19px;border-color:#345b67;background:linear-gradient(110deg,#142840,#17283a);padding:17px 21px" aria-label="Daily automatic feed">
 <div class="top" style="align-items:center;gap:10px"><div><div class="eyebrow">PUBLIC EMPLOYER FEEDS · DAILY AUTO-REFRESH</div><h2 style="margin:7px 0;font-size:18px">Automatic vacancy updates</h2><div id="feedState" style="font-size:13px;color:#c6d5e8;line-height:1.6" aria-live="polite">Checking for published vacancies…</div></div><div class="footlinks"><button class="btn primary" id="refreshFeed">↻ Refresh list</button><label class="btn"><input type="checkbox" id="liveOnly" style="accent-color:#61d6a5"/> Only auto-feed jobs</label></div></div>
 <div id="sourceHealth" style="font-size:12px;color:#9fb1cb;margin-top:11px"></div>
 <p style="color:#b3c5db;font-size:11px;margin-bottom:0">A source can fail independently; the dashboard displays its status. “Remote” is not proof that Romania is eligible. Live sources: public Lever, Greenhouse, SmartRecruiters and Recruitee feeds when accessible. LinkedIn remains a manual search link.</p>
</section>
'''
assert anchor in src
src=src.replace(anchor,banner+anchor)
src=src.replace('Use the discovery hub above for 30+ sources and European studios. These are one-click shortcuts for a quick weekly check.','Use the discovery hub for LinkedIn, Google and 30+ employer/search links, including vacancies unavailable via automatic APIs.')
src=src.replace('<h2>🗓 Weekly check</h2><p><strong>Every Monday · around 8:00 AM</strong><br>Europe/Bucharest timezone</p><p>Your ChatGPT job-watch task runs separately. Review any new results there, then add promising jobs to this tracker.</p>', '<h2>🗓 Daily job watch</h2><p><strong>Every day · around 8:00 AM</strong><br>Europe/Bucharest timezone</p><p>The separate ChatGPT job-watch report checks broader sources; GitHub Pages refreshes the supported employer feeds separately. They are not directly synchronized.</p>')
src=src.replace('it does not remove the V3 vacancies.', 'it does not remove your existing opportunities.')
src=src.replace('Multi-source discovery · Standalone HTML · No account or installation needed · External vacancy links and search engines may change or close. Verify eligibility, dates, salary and application availability directly with the employer. Updated and selected job pages checked: 22 October 2026. CV fit rankings are editorial, not automated ATS scores.', 'Daily Live build · Hosting is required for the auto-feed to work · The curated starting leads were checked on 22 October 2026 and may now be expired. Public ATS jobs are checked by the GitHub Action on its last successful run. CV fit is an editorial estimate; verify each application and country eligibility directly.')
src=src.replace('function render(){const q=',"function render(){const q=")
needle="const filtered=jobs.filter(j=>{const matchesGeo="
assert needle in src
src=src.replace(needle,"const filtered=jobs.filter(j=>{if(document.getElementById('liveOnly')?.checked&&!j.liveFeed)return false;const matchesGeo=")
needle="for(const j of filtered){const root=element('article','job');"
assert needle in src
src=src.replace(needle,"for(const j of filtered.slice().sort((a,b)=>Number(!!b.liveFeed)-Number(!!a.liveFeed)||String(b.firstSeen||'').localeCompare(String(a.firstSeen||'')))){const root=element('article','job');")
needle="[j.checked?'Listing checked '+j.checked:'Older lead · recheck vacancy',j.checked?'':'warning']];"
assert needle in src
src=src.replace(needle,"[j.liveFeed?'Visible in latest employer feed · '+j.checked:(j.checked?'Historical check '+j.checked:'Historical lead · recheck'),j.liveFeed?'remote':'warning'],[j.firstSeen?'First seen '+j.firstSeen:'','']].filter(x=>x[0]);")
needle="$('exportCsv').onclick=()=>{"
assert needle in src
newjs=r'''/* Website feed: separate from the ChatGPT scheduled task. */
const FEED_URL='data/jobs.json';
const normalizeLink=(v)=>{try{const u=new URL(v);return u.hostname.toLowerCase()+u.pathname.replace(/\/$/,'').toLowerCase()}catch{return ''}};
async function loadFeed(){
  const state=$('feedState'),health=$('sourceHealth');
  state.textContent='Loading the latest published snapshot…';
  try{
    const response=await fetch(FEED_URL+'?t='+Date.now(),{cache:'no-store'});
    if(!response.ok)throw Error('Feed response '+response.status);
    const data=await response.json();
    if(!Array.isArray(data.jobs)||!Array.isArray(data.sources))throw Error('Invalid feed format');
    const seen=new Set(),byId=new Map(jobs.map(x=>[x.id,x]));
    const byLink=new Map(jobs.filter(x=>x.url).map(x=>[normalizeLink(x.url),x]));
    for(const entry of data.jobs){
      if(!entry||typeof entry.id!=='string'||!safeUrl(entry.url)||typeof entry.company!=='string'||typeof entry.title!=='string')continue;
      seen.add(entry.id);
      const old=byId.get(entry.id)||byLink.get(normalizeLink(entry.url));
      if(old){
        seen.add(old.id);
        const saved=old.saved,status=old.status,notes=old.notes;
        Object.assign(old,entry,{id:old.id,saved,status,notes:notes||entry.notes,liveFeed:entry.liveFeed!==false});
        // Preserve stable tracking ID for manually curated opportunities.
      }else{
        const item={...entry,saved:false,status:'not-started'};
        jobs.push(item);byId.set(item.id,item);
      }
    }
    const good=data.sources.filter(s=>s.ok),bad=data.sources.filter(s=>!s.ok);
    const completeNames=new Set(good.map(s=>s.company));
    for(const j of jobs){
      if(j.sourceKind==='automatic'&&!seen.has(j.id)&&completeNames.has(j.company)){
        j.liveFeed=false;
        if(!j.notes?.includes('NOT in latest'))j.notes=(j.notes||'')+' NOT in latest successful employer feed — may have closed.';
      }
    }
    const count=jobs.filter(j=>j.liveFeed).length;
    let when='Not run yet';
    if(data.checked_at){const d=new Date(data.checked_at);if(!Number.isNaN(+d))when=d.toLocaleString('en-GB',{timeZone:'Europe/Bucharest',day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'})+' Romania time';}
    state.textContent=(data.checked_at?`Last feed run: ${when}. `:'Awaiting first scheduled refresh. ')+`${count} current ATS-listed matching job(s) shown; ${good.length} sources succeeded, ${bad.length} unavailable.`;
    health.textContent=data.sources.length?data.sources.map(s=>`${s.ok?'✓':'⚠'} ${s.company}: ${s.ok?s.matches+' matches':'unavailable'}`).join('   ·   '):'Automatic feeds activate after the first GitHub Actions run.';
    if(bad.length)health.textContent+=' · Unavailable sources do not count as a confirmed no-jobs result.';
    persist();render();
  }catch(e){
    state.textContent=location.protocol==='file:'?'Offline HTML mode: automatic imports require the hosted GitHub Pages version. Existing jobs and search links still work.':'Feed unavailable: displaying locally saved and curated leads. '+e.message;
    health.textContent='The daily ChatGPT job-watch report is independent of this page.';
  }
}
$('refreshFeed').addEventListener('click',loadFeed);
$('liveOnly').addEventListener('change',render);
'''
src=src.replace(needle,newjs+needle)
src=src.replace('};render();\n</script></body></html>', '};render();loadFeed();\n</script></body></html>')
assert 'render();loadFeed();' in src
# The original JS has two occurrences of the key function; checked above.
dst.write_text(src,encoding='utf-8')
print(dst, len(src))
