// Original managed launcher. The engine attaches to the app-owned Chrome;
// this process neither opens a second browser nor exposes a public server.
import {pathToFileURL} from 'node:url';
import {resolve} from 'node:path';
if(process.env.VSO_FLOW_ATTACH_ONLY!=='1')throw Error('Attach-only mode required');
const root=process.env.VSO_FLOW_ENGINE_ROOT;
if(!root||!root.startsWith('/'))throw Error('Complete Flow engine is not installed');
const {LocalCore}=await import(pathToFileURL(resolve(root,'dist/core.js')));
const {startServer}=await import(pathToFileURL(resolve(root,'dist/server.js')));
const role=await startServer(new LocalCore());
if(role!=='owner')throw Error('Managed engine port already has an owner; refusing another queue');
console.log('Private managed Flow engine ready');
