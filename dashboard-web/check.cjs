// Run with the dashboard running: node dashboard-web/check.cjs
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const path=require('node:path');
const fs=require('node:fs/promises');
const base=process.env.NFL_DASHBOARD_URL||'http://localhost:8054';
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1050}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const response=await page.request.get(base+'/api/data',{timeout:120000});assert.equal(response.status(),200);
  const data=await response.json();
  assert(data.team_rankings.length>0);
  assert.equal((await page.request.get(base+'/.env')).status(),404);
  await page.goto(base);await page.locator('.hero').waitFor();
  assert.equal(await page.title(),'NFL Analytics');
  assert.equal(await page.locator('.team-logo').first().evaluate(i=>getComputedStyle(i).backgroundColor),'rgba(0, 0, 0, 0)');
  await page.locator('.player-headshot').first().evaluate(i=>i.decode());
  await page.locator('.hero .team-logo').evaluate(i=>i.decode());
  await page.evaluate(async()=>{for(const team of teams()){const i=new Image();i.src=teamLogos[team.team];await i.decode();}});
  await page.locator('[data-sort="team_name"]').click();
  const alphabetical=[...data.team_rankings].sort((a,b)=>a.team_name.localeCompare(b.team_name));
  assert((await page.locator('tbody tr').first().innerText()).includes(alphabetical[0].team_name));
  await page.locator('[data-sort="power_rank"]').click();
  const out=path.join(__dirname,'../docs/portfolio/gridiron');await fs.mkdir(out,{recursive:true});
  await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(out,'overview.png'),fullPage:true});
  await page.locator('.hero [data-team]').click();await page.locator('.detail').waitFor();
  await page.locator('.detail .team-logo').evaluate(i=>i.decode());
  await page.locator('.detail').screenshot({path:path.join(out,'team-detail.png')});
  await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(out,'teams.png'),fullPage:false});
  await page.locator('[data-conf="AFC"]').click();
  await page.locator('#search').fill('Patriots');
  assert.equal(await page.locator('.panel').first().locator('tbody tr').count(),1);
  const downloadPromise=page.waitForEvent('download');await page.locator('#export').click();
  const download=await downloadPromise;const file=await download.path();const csv=await fs.readFile(file,'utf8');
  assert(csv.includes('New England Patriots'));assert(!csv.includes('Seattle Seahawks'));
  await page.locator('nav a[href="#players"]').click();
  for(const cat of ['Passing','Rushing','Receiving','Defense','Kicking']){
   await page.locator(`[data-category="${cat}"]`).click();
   assert(await page.locator('tbody tr').count()>0);
   if(cat==='Passing'||cat==='Defense'){await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(out,cat==='Passing'?'leaders.png':'defense.png'),fullPage:false});}
  }
  await page.locator('[data-category="Passing"]').click();
  await page.locator('#metric').selectOption('passing_touchdowns');
  assert((await page.locator('.panel h2').first().innerText()).includes('Pass TD'));
  await page.locator('#metric').selectOption('passing_yards');
  const top=data.player_passing_leaders.sort((a,b)=>b.passing_yards-a.passing_yards)[0];
  await page.locator('#search').fill('zzzz-no-player');assert(await page.locator('.empty').count()>0);
  await page.locator('#search').fill(top.player_name);await page.locator('tbody [data-player]').first().click();
  await page.locator('#profile-a').waitFor();
  assert.equal(await page.locator('#profile-a').inputValue(),top.player_id);
  assert((await page.locator('#content').innerText()).includes('Career accolades'));
  const expected=data.player_passing_by_week.filter(r=>r.player_id===top.player_id).reduce((n,r)=>n+r.passing_yards,0);
  assert.equal(expected,top.passing_yards);
  await page.locator('.player-headshot.large').evaluate(i=>i.decode());
  await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(out,'player.png'),fullPage:true});
  await page.locator('[data-profile-mode="compare"]').click();
  await page.locator('#compare-category').selectOption('Rushing');
  assert.equal(await page.locator('.comparison-split article').count(),2);
  assert.equal(await page.locator('.comparison-split .player-headshot').count(),2);
  await Promise.all((await page.locator('.comparison-split .player-headshot').elementHandles()).map(i=>i.evaluate(img=>img.decode())));
  assert(await page.locator('.compare-row').count()>0);
  await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(out,'comparison.png'),fullPage:true});
  await page.locator('nav a[href="#pipeline"]').click();assert((await page.locator('#content').innerText()).includes('49/49'));
  await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(out,'pipeline.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});
  for(const view of ['overview','teams','players','profiles','pipeline']){
   await page.locator(`nav a[href="#${view}"]`).click();
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),view+' overflows mobile');
  }
  await page.locator('nav a[href="#overview"]').click();await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(out,'mobile.png'),fullPage:true});
  await page.route('**/api/data',route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:'Test connection unavailable'})}));
  await page.locator('#refresh').click();await page.waitForFunction(()=>document.querySelector('#notice').textContent.includes('Test connection unavailable'));
  assert((await page.locator('#notice').innerText()).includes('previously loaded'));
  await page.unroute('**/api/data');await page.locator('#refresh').click();await page.waitForFunction(()=>document.querySelector('#notice').textContent==='');
  assert.deepEqual(errors,[]);
  console.log('PASS: real data, team logos, filters, CSV, five leaderboards, player profiles/comparison, error recovery, desktop and mobile.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
