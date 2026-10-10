/** Structural result controls only; no native evidence qualification. */
const {default:Ajv}=await import(process.argv[2]);const root='docs/helix/02-design/contracts/';
const ajv=new Ajv({strict:true}).addSchema(await Bun.file(root+'acceptance-input-v0.1.schema.json').json());
const schema=await Bun.file(root+'key-migration-result-v0.1.schema.json').json();const validate=ajv.compile(schema);const reconcile=ajv.compile({$ref:schema.$id+'#/$defs/reconciliation'});
const artifact={identity:'fixture',bytesBase64:'eA==',sha256:'0'.repeat(64)};const pin={identity:'fixture',version:'0.1.0',sha256:'0'.repeat(64)};
const attempt={kind:'installed',databaseIdentity:'db',schemaName:'truss',installationId:'install',sourceEpoch:'epoch',migrationAttemptId:'attempt',procedure:pin,originalRequest:artifact};
const assessment={state:'complete',observation:artifact,sourceInventory:artifact,targetCorrespondence:artifact,verdict:{state:'collision_free'}};
const committed={outcome:'migrated',commit:{originalAttempt:attempt,receipt:artifact,commitObservation:artifact,committedBinding:artifact,installedInventory:artifact,assessment}};
let cases=0;const failures:string[]=[];const probe=(name:string,value:any,expected:boolean,fn=validate)=>{cases++;if(Boolean(fn(value))!==expected)failures.push(name);};
probe('complete migrated shape',committed,true);
probe('pre-native refusal',{outcome:'refused',reason:'profile',containment:{phase:'pre_native'}},true);
probe('confirmed rollback',{outcome:'rolled_back',originalAttempt:attempt,failedStage:'target_staging',terminationEvidence:artifact},true);
probe('unknown commit',{outcome:'commit_unknown',originalAttempt:attempt,originalEvidence:artifact,recoveryReference:'original'},true);
probe('cleanup recovery',{outcome:'recovery_required',reason:'cleanup_unknown',failedStage:'binding_switch',originalAttempt:attempt,originalEvidence:artifact,recoveryReference:'original'},true);
probe('unknown with committed payload',{outcome:'commit_unknown',originalAttempt:attempt,originalEvidence:artifact,recoveryReference:'original',commit:committed.commit},false);
probe('missing containment',{outcome:'refused',reason:'collision'},false);
probe('missing cleanup stage',{outcome:'recovery_required',reason:'cleanup_unknown',originalAttempt:attempt,originalEvidence:artifact,recoveryReference:'original'},false);
probe('authorization refusal no assessment',{outcome:'refused',reason:'authorization',containment:{phase:'pre_native'}},true);
probe('authorization refusal cannot leak assessment',{outcome:'refused',reason:'authorization',containment:{phase:'pre_native'},assessment},false);
const blocked=structuredClone(committed);blocked.commit.assessment.verdict={state:'blocked'} as any;probe('blocked committed assessment',blocked,false);
const incomplete=structuredClone(committed);incomplete.commit.assessment={state:'incomplete',reason:'resource',diagnostics:artifact} as any;probe('incomplete committed assessment',incomplete,false);
probe('observation unavailable',{outcome:'observation_unavailable',reason:'custody'},true,reconcile);
probe('reconcile cannot clean-refuse',{outcome:'refused',reason:'profile',containment:{phase:'pre_native'}},false,reconcile);
probe('unavailable carries invented attempt',{outcome:'observation_unavailable',reason:'custody',originalAttempt:attempt},false,reconcile);
probe('shape-valid forged evidence',committed,true); // Byte/profile/native admission must reject this fixture.
const receipt={scope:'Result/reconciliation structural probes; no custody/native/commit qualification',cases,failures};await Bun.write('docs/helix/04-build/evidence/design-audit/key-migration-result.json',JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));if(failures.length)process.exit(1);
