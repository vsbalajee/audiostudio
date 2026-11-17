import assert from "node:assert/strict";
const BASE=(process.env.AUDIO_STUDIO_URL||"https://audiostudio.vsbalaajee.workers.dev").replace(/\/$/,"");
const endpoint=BASE+"/mcp";
let reqCount=0;
async function rpc(method, params, options={}) {
  const id=++reqCount;
  const headers={Accept:"application/json, text/event-stream","Content-Type":"application/json",...(options.headers||{})};
  const resp=await fetch(endpoint,{method:"POST",headers,body:JSON.stringify({jsonrpc:"2.0",id,method,params}),redirect:"manual",signal:AbortSignal.timeout(15000)});
  const body=await resp.text();
  assert.equal(resp.status,200,method+": status="+resp.status+" body="+body.slice(0,500));
  const payload=resp.headers.get("content-type")?.includes("text/event-stream")
    ? JSON.parse(body.split(/\r?\n/).filter(x=>x.startsWith("data:")).at(-1).slice(5).trim())
    : JSON.parse(body);
  assert.equal(payload.jsonrpc,"2.0");
  assert.equal(payload.id,id);
  assert.ok(!payload.error,JSON.stringify(payload.error));
  return payload;
}
const tests={
  "initialize_2024_11_05":async()=> {let x=await rpc("initialize",{protocolVersion:"2024-11-05",capabilities:{},clientInfo:{name:"chatgpt-compat",version:"1.0"}});assert.ok(x.result.serverInfo);console.log("protocol:",x.result.protocolVersion)},
  "initialize_2025_03_26":async()=> {let x=await rpc("initialize",{protocolVersion:"2025-03-26",capabilities:{},clientInfo:{name:"chatgpt-compat",version:"1.0"}});assert.ok(x.result.serverInfo);console.log("protocol:",x.result.protocolVersion)},
  "initialize_2025_06_18":async()=> {let x=await rpc("initialize",{protocolVersion:"2025-06-18",capabilities:{},clientInfo:{name:"chatgpt-compat",version:"1.0"}});assert.ok(x.result.serverInfo);console.log("protocol:",x.result.protocolVersion)},
  "initialize_2025_11_25":async()=> {let x=await rpc("initialize",{protocolVersion:"2025-11-25",capabilities:{},clientInfo:{name:"chatgpt-compat",version:"1.0"}});assert.ok(x.result.serverInfo);console.log("protocol:",x.result.protocolVersion)},
  "initialize_client_sdk_none":async()=> {let x=await rpc("initialize",{protocolVersion:"2025-06-18",capabilities:{tools:{}},clientInfo:{name:"chatgpt",version:"1.0"}},{headers:{"MCP-Protocol-Version":"2025-06-18"}});assert.ok(x.result.serverInfo);console.log("capabilities:",JSON.stringify(x.result.capabilities));},
  "tools_list_chatgpt_headers":async()=> {let x=await rpc("tools/list",{}, {headers:{"MCP-Protocol-Version":"2025-06-18"}});assert.equal(x.result.tools?.length,3);for(const t of x.result.tools){assert.ok(t.name&&t.description&&t.inputSchema);assert.equal(t.inputSchema.type,"object");console.log("Tool:",t.name,JSON.stringify(t.inputSchema).slice(0,900))}},
  "tools_call_start":async()=>{let x=await rpc("tools/call",{name:"start_audio_studio",arguments:{project_name:"ChatGPT Test"}});assert.equal(JSON.parse(x.result.content[0].text).status,"browser_form_ready")},
  "tools_call_defaults":async()=>{let x=await rpc("tools/call",{name:"get_audio_studio_defaults",arguments:{}});assert.ok(JSON.parse(x.result.content[0].text).defaults)},
  "rpc_get_sse_optional":async()=>{
    const response=await fetch(endpoint,{headers:{Accept:"text/event-stream","MCP-Protocol-Version":"2025-06-18"},signal:AbortSignal.timeout(15000)});
    const body=await response.text();
    // Stateless Streamable HTTP may use 405 for GET.
    assert.ok([200,405].includes(response.status),"unexpected GET: "+response.status+" "+body.slice(0,300));
    console.log("GET status=",response.status,"Content-Type=",response.headers.get("content-type"));
  }
};
const name=process.argv[2];if(!tests[name])throw new Error("Unknown case "+name);
await tests[name]();console.log("PASS "+name);
