import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { chromium } from "playwright";
const URL = process.env.AUDIO_STUDIO_URL || "http://127.0.0.1:8787";
function wav(seconds, frequency = 440) {
  const sampleRate = 8000, num = Math.round(seconds * sampleRate), bytes = 44 + 2 * num;
  const b = Buffer.alloc(bytes);
  b.write("RIFF", 0); b.writeUInt32LE(bytes-8,4); b.write("WAVEfmt ",8);
  b.writeUInt32LE(16,16); b.writeUInt16LE(1,20); b.writeUInt16LE(1,22);
  b.writeUInt32LE(sampleRate,24); b.writeUInt32LE(sampleRate*2,28);
  b.writeUInt16LE(2,32); b.writeUInt16LE(16,34);
  b.write("data",36); b.writeUInt32LE(num*2,40);
  for(let i=0;i<num;i++) b.writeInt16LE(Math.round(3000*Math.sin(i*2*Math.PI*frequency/sampleRate)),44+i*2);
  return b;
}
async function rpc(method, id, params){
  const response=await fetch(URL+"/mcp",{method:"POST",headers:{Accept:"application/json, text/event-stream","Content-Type":"application/json","MCP-Protocol-Version":"2025-06-18"},body:JSON.stringify({jsonrpc:"2.0",id,method,params})});
  const txt=await response.text();
  assert.equal(response.status,200,txt.slice(0,1000));
  return response.headers.get("content-type")?.includes("text/event-stream")?JSON.parse(txt.split(/\r?\n/).filter(x=>x.startsWith("data:")).at(-1).slice(5).trim()):JSON.parse(txt);
}
const init=await rpc("initialize",1,{protocolVersion:"2025-06-18",capabilities:{},clientInfo:{name:"CI",version:"1"}});
assert.equal(init.result.serverInfo.name,"audio-studio");
const list=await rpc("tools/list",2,{});
const names=list.result.tools.map(x=>x.name);
for(const n of ["create_audio_project","edit_audio_project","start_audio_studio"])assert.ok(names.includes(n),"Missing MCP "+n);
const created=await rpc("tools/call",3,{name:"create_audio_project",arguments:{project:{project_name:"Chat MP3 QA",voice_files:["clip-1.wav"],music_level:"quiet"}}});
const createState=JSON.parse(created.result.content[0].text);
assert.deepEqual(createState.project.voice_files,["clip-1.wav"]);
const edited=await rpc("tools/call",4,{name:"edit_audio_project",arguments:{project:createState.project,action:"add_voice",filename:"clip-2.wav"}}); 
const editState=JSON.parse(edited.result.content[0].text);
assert.deepEqual(editState.project.voice_files,["clip-1.wav","clip-2.wav"]);
const moved=await rpc("tools/call",5,{name:"edit_audio_project",arguments:{project:editState.project,action:"move_voice",from_position:2,position:1}});
const moveState=JSON.parse(moved.result.content[0].text);
assert.deepEqual(moveState.project.voice_files,["clip-2.wav","clip-1.wav"]);
const changed=await rpc("tools/call",6,{name:"edit_audio_project",arguments:{project:moveState.project,action:"update_setting",setting:"after_intro_seconds",value:1}});
const chatConfig=JSON.parse(changed.result.content[0].text);
assert.equal(chatConfig.project.after_intro_seconds,1);
console.log("PASS MCP chat project creation, add, move, settings update");
const browser=await chromium.launch({headless:true});
try{
const context=await browser.newContext({acceptDownloads:true});const page=await context.newPage();
const errors=[];
page.on("pageerror",e=>errors.push(e.message));
const response=await page.goto(chatConfig.app_url,{waitUntil:"networkidle",timeout:25000});
assert.equal(response.status(),200);
assert.equal(await page.locator("#project").inputValue(),"Chat MP3 QA");
assert.equal(await page.locator("#firstGap").inputValue(),"1");
assert.match(await page.locator("#chatPlan").innerText(),/clip-2\.wav, clip-1\.wav/);
const encoderStatus=await page.evaluate(()=>({renderer:typeof window.AudioStudioRender?.renderProject,encoder:typeof window.lamejs?.Mp3Encoder}));
assert.deepEqual(encoderStatus,{renderer:"function",encoder:"function"});
await page.locator("#voices").setInputFiles([
 {name:"clip-1.wav",mimeType:"audio/wav",buffer:wav(1.2,330)},
 {name:"clip-2.wav",mimeType:"audio/wav",buffer:wav(1.5,550)}
]);
await page.waitForFunction(()=>document.querySelectorAll("#files .file").length===2);
assert.match(await page.locator("#files .file").first().innerText(),/clip-2\.wav/);
await page.locator("#music").setInputFiles({name:"music.wav",mimeType:"audio/wav",buffer:wav(1.1,220)});
await page.locator("#preview").click();
const timeline=await page.locator("#timeline").innerText();
assert.match(timeline,/clip-2\.wav/);
assert.match(timeline,/Estimated total:/);
const [dl] = await Promise.all([
 page.waitForEvent("download",{timeout:120000}),
 page.locator("#render").click()
]);
assert.match(dl.suggestedFilename(),/Chat_MP3_QA_FINAL\.mp3/);
const path=await dl.path();
const probe=JSON.parse(execFileSync("ffprobe",["-v","error","-show_entries","format=duration,size:stream=codec_name,bit_rate,sample_rate,channels","-of","json",path],{encoding:"utf-8"}));
assert.ok(probe.format.duration>3.5 && probe.format.duration<9,JSON.stringify(probe));
const audio=probe.streams.find(x=>x.codec_name==="mp3");
assert.ok(audio,JSON.stringify(probe));
assert.equal(Number(audio.sample_rate),48000);
assert.equal(Number(audio.channels),2);
assert.ok(Number(probe.format.size)>1000);
assert.deepEqual(errors,[]);
console.log("PASS Browser MP3 downloaded:",dl.suggestedFilename(),"duration:",probe.format.duration,"size:",probe.format.size,"bytes");
await context.close();
}finally{await browser.close();}
