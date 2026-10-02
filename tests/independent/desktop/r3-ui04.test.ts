import {expect,test} from 'vitest';
import {compileRegistry} from '../../../apps/desktop/src/modules/registry';

test('R3-UI04-ASCII-01 | module ID with a terminal newline is not a canonical ASCII identifier',()=>{
  const contribution={moduleId:'virtual_left\n',version:'1.0.0',hostUiMajor:1,
    expectedApiPrefixes:['/api/v1/virtual_left'],navigation:{label:'Virtual',order:1},
    routes:[{routeId:'virtual_left_route',path:'/virtual_left'}],
    agentPanel:{profileId:'virtual_left.assistant@1',title:'Virtual'},
    settings:[{key:'virtual_left_setting',schemaVersion:1}],
    companion:{appearanceId:'virtual_left_pet',label:'Virtual'}};
  const before=JSON.stringify(contribution);
  let actual='rejected';let returnedId:string|null=null;
  try{const registry=compileRegistry([contribution]);actual=`accepted:${registry.length}`;returnedId=registry[0]?.moduleId??null;}
  catch{actual='rejected';}
  console.log(JSON.stringify({caseId:'R3-UI04-ASCII-01',inputModuleId:contribution.moduleId,
    expected:'rejected',actual,returnedModuleId:returnedId,inputUnchanged:JSON.stringify(contribution)===before,data:'virtual_only'}));
  expect(actual).toBe('rejected');
});
