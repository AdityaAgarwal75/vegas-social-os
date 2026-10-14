/* Real official MCP SDK transport; OAuth token is supplied privately by the test harness. */
import {pathToFileURL} from 'node:url';
const root=process.env.VSO_MCP_SDK_ROOT;
if(!root)throw Error('Set VSO_MCP_SDK_ROOT to an installed official SDK dist/esm directory');
const {Client}=await import(pathToFileURL(root+'/client/index.js'));
const {StreamableHTTPClientTransport}=await import(pathToFileURL(root+'/client/streamableHttp.js'));
const token=process.env.VSO_TEST_TOKEN;
if(!token)throw Error('OAuth test token missing; never print it');
const client=new Client({name:'vegas-social-os-acceptance',version:'0.7.0'});
const transport=new StreamableHTTPClientTransport(new URL(process.env.VSO_TEST_MCP),{requestInit:{headers:{Authorization:'Bearer '+token}}});
try{
 await client.connect(transport);
 const listed=await client.listTools();
 for(const name of ['doctor','account_list','guide','onboarding_status','workflow_audit']){
  const r=await client.callTool({name,arguments:{}});if(r.isError)throw Error(name+' returned an error');
 }
 const draft=await client.callTool({name:'channel_save',arguments:{name:'Disposable MCP acceptance','niche':'Private test draft; never publish',language:'English',account_ids:[]}});
 if(draft.isError||!draft.structuredContent?.id)throw Error('Harmless draft write failed');
 console.log(JSON.stringify({official_sdk:true,authenticated_read_tools:5,harmless_disposable_draft:true,discovered_tools:listed.tools.length}));
}finally{await client.close();}
