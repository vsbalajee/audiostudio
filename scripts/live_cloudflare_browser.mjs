import assert from "node:assert/strict";
import { chromium } from "playwright";
const base = process.env.AUDIO_STUDIO_URL || "https://audiostudio.vsbalaajee.workers.dev";
function wav(seconds, frequency=440) {
  const sampleRate = 8000, numSamples = Math.round(seconds*sampleRate), bytes=44+numSamples*2;
  const b=Buffer.alloc(bytes);
  b.write("RIFF",0);b.writeUInt32LE(bytes-8,4);b.write("WAVEfmt ",8);
  b.writeUInt32LE(16,16);b.writeUInt16LE(1,20);b.writeUInt16LE(1,22);
  b.writeUInt32LE(sampleRate,24);b.writeUInt32LE(sampleRate*2,28);
  b.writeUInt16LE(2,32);b.writeUInt16LE(16,34);
  b.write("data",36);b.writeUInt32LE(numSamples*2,40);
  for(let i=0;i<numSamples;i++)b.writeInt16LE(Math.floor(2500*Math.sin(i*2*Math.PI*frequency/sampleRate)),44+i*2);
  return b;
}
let browser; let failures=0;
async function test(name,fn) {try{const result=await fn(); console.log("PASS "+name+(result?": "+result:""));}catch(e){failures++;console.error("FAIL "+name+": "+(e.stack||e));}}
try {
  browser=await chromium.launch({headless:true});
  const context=await browser.newContext({acceptDownloads:true});
  const page=await context.newPage();
  const errors=[];page.on("pageerror",e=>errors.push(e.message));
  await test("Open real browser interface",async()=>{
    const response=await page.goto(base+"/",{waitUntil:"networkidle",timeout:30000});
    assert.equal(response.status(),200);
    assert.match(await page.title(),/Audio Studio/);
    assert.equal(await page.locator("#project").inputValue(),"My Audio Project");
  });
  await test("Project name from MCP browser link",async()=>{
    await page.goto(base+"/?project=QA%20Browser",{waitUntil:"networkidle"});
    assert.equal(await page.locator("#project").inputValue(),"QA Browser");
  });
  await test("Select 2 recordings",async()=>{
    await page.locator("#voices").setInputFiles([
      {name:"02-closing.wav",mimeType:"audio/wav",buffer:wav(2,660)},
      {name:"01-opening.wav",mimeType:"audio/wav",buffer:wav(1,440)}
    ]);
    await page.waitForTimeout(2500);
    assert.equal(await page.locator("#files .file").count(),2);
    assert.match(await page.locator("#files .file").first().innerText(),/02-closing/);
  });
  await test("Natural filename sort",async()=>{
    await page.locator("#sort").click();
    assert.match(await page.locator("#files .file").first().innerText(),/01-opening/);
  });
  await test("Reorder clips using button",async()=>{
    await page.locator("#files .file").last().getByRole("button",{name:"↑"}).click();
    assert.match(await page.locator("#files .file").first().innerText(),/02-closing/);
    await page.locator("#sort").click();
  });
  await test("Gap and music settings",async()=>{
    await page.locator("#firstGap").fill("3");
    await page.locator("#gap").fill("3");
    await page.locator("#music").setInputFiles({name:"background.wav",mimeType:"audio/wav",buffer:wav(2,220)});
    await page.locator("#musicLevel").selectOption("quiet");
    assert.match(await page.locator("#musicName").innerText(),/background.wav/);
  });
  await test("Timeline preview and duration",async()=>{
    await page.locator("#preview").click();
    const text=await page.locator("#timeline").innerText();
    for(const expected of ["01-opening.wav","02-closing.wav","3 second gap","background.wav","Quiet"]) {
      assert.ok(text.toLowerCase().includes(expected.toLowerCase()),"Timeline missing "+expected+" in "+text);
    }
    assert.match(text,/Estimated total:/);
  });
  await test("Download settings JSON",async()=>{
    const [download]=await Promise.all([page.waitForEvent("download"),page.locator("#download").click()]);
    const stream=await download.createReadStream(),chunks=[];
    for await (const chunk of stream)chunks.push(chunk);
    const value=JSON.parse(Buffer.concat(chunks).toString("utf8"));
    assert.equal(value.project_name,"QA Browser");
    assert.deepEqual(value.voice_files,["01-opening.wav","02-closing.wav"]);
    assert.equal(value.music_file,"background.wav");
    assert.equal(value.after_intro_seconds,3);
    assert.equal(value.mute_music_during_final_voice,true);
    assert.equal(value.rendered,false);
  });
  await test("MP3 rendering accurately disabled",async()=>{
    const button=page.getByRole("button",{name:/Generate MP3/});
    assert.equal(await button.isDisabled(),true);
  });
  await test("No uncaught browser errors",async()=>{assert.deepEqual(errors,[])});
  await context.close();
}finally{if(browser)await browser.close()}
console.log("Browser test failure count:",failures);
process.exitCode=failures?1:0;
