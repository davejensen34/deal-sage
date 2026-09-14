export type ReviewItem={slot:string;signal_type:string;requested_state:string;as_of:string;model:string;
  sources:{source_id:string;url:string;text:string}[];summary:string;questions:string[];contradictions:string[];
  supported_source_ids:string[];model_dimensions:Record<string,string>;assessment:Record<string,string>;
  review_context:{reviewer:string;review_kind:string;operating_supported_on:string|null;
    operating_source_ids:string[];geography_basis:string;geography_state:string|null;geography_source_ids:string[]}};
export type ReviewPackage={version:'m7-analyst-review-package-v1';result_sha256:string;bundle_sha256:string;items:ReviewItem[]};
export type Feedback={usefulness:''|'useful'|'not_useful'|'defer';rationale:string;review_minutes:string};
export const MAX_PACKAGE_BYTES=2_000_000;
const object=(v:unknown):v is Record<string,unknown>=>typeof v==='object'&&v!==null&&!Array.isArray(v);
const text=(v:unknown):v is string=>typeof v==='string'&&v.length<=100_000;
const strings=(v:unknown):v is string[]=>Array.isArray(v)&&v.length<=100&&v.every(text);
const map=(v:unknown):v is Record<string,string>=>object(v)&&Object.keys(v).length<=30&&Object.values(v).every(text);
const hash=(v:unknown):v is string=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);

export function parseReviewPackage(raw:string):ReviewPackage{
  if(new TextEncoder().encode(raw).length>MAX_PACKAGE_BYTES)throw new Error('Package exceeds the 2 MB limit.');
  let data:unknown;
  try{data=JSON.parse(raw)}catch{throw new Error('Select a valid evaluation review JSON package.')}
  if(!object(data)||data.version!=='m7-analyst-review-package-v1'||!hash(data.result_sha256)||!hash(data.bundle_sha256)||
     !Array.isArray(data.items)||!data.items.length||data.items.length>20)throw new Error('Unsupported evaluation review package.');
  const slots=new Set<string>();
  for(const item of data.items){
    if(!object(item)||!['slot','signal_type','requested_state','as_of','model','summary'].every(k=>text(item[k]))||
       !strings(item.questions)||!strings(item.contradictions)||!strings(item.supported_source_ids)||
       !map(item.model_dimensions)||!map(item.assessment)||!object(item.review_context)||
       !Array.isArray(item.sources)||!item.sources.length||item.sources.length>20)throw new Error('Invalid review item.');
    if(!(item.slot as string).trim()||slots.has(item.slot as string))throw new Error('Review slots must be distinct.');
    slots.add(item.slot as string);
    const sourceIds=new Set<string>();
    for(const source of item.sources){
      if(!object(source)||!text(source.source_id)||!source.source_id.trim()||sourceIds.has(source.source_id)||
         !text(source.url)||!text(source.text))throw new Error('Invalid evidence entry.');
      sourceIds.add(source.source_id);
    }
    const ctx=item.review_context;
    if(!['reviewer','review_kind','geography_basis'].every(k=>text(ctx[k]))||
       !(ctx.operating_supported_on===null||text(ctx.operating_supported_on))||
       !(ctx.geography_state===null||text(ctx.geography_state))||
       !strings(ctx.operating_source_ids)||!strings(ctx.geography_source_ids)||
       !['version','temporal_scope','operating_status_at_assessment','requested_state_operating_fit','deterministic_research_disposition'].every(k=>text((item.assessment as Record<string,unknown>)[k])))throw new Error('Invalid contextual assessment.');
    if([...item.supported_source_ids,...ctx.operating_source_ids,...ctx.geography_source_ids].some(id=>!sourceIds.has(id)))throw new Error('Review cites evidence missing from this package.');
  }
  // Shape validation is not source authentication. Feedback binds the exact
  // selected file bytes, including fields this UI does not interpret.
  return data as ReviewPackage;
}

export function feedbackRecord(pkg:ReviewPackage,packageHash:string,reviewer:string,feedback:Record<string,Feedback>){
  if(!hash(packageHash)||!reviewer.trim()||reviewer.length>200)throw new Error('Enter your name (up to 200 characters).');
  const judgments=pkg.items.flatMap(item=>{
    const value=feedback[item.slot];
    if(!value?.usefulness)return [];
    if(!['useful','not_useful','defer'].includes(value.usefulness)||value.rationale.trim().length<3||value.rationale.length>4000)throw new Error('Add a rationale for each selected judgment (3–4,000 characters).');
    const minutes=value.review_minutes.trim()===''?null:Number(value.review_minutes);
    if(minutes!==null&&(!Number.isFinite(minutes)||minutes<0||minutes>1440))throw new Error('Review minutes must be between 0 and 1,440, or blank.');
    return [{slot:item.slot,usefulness:value.usefulness,rationale:value.rationale.trim(),
      self_reported_review_seconds:minutes===null?null:Math.round(minutes*60)}];
  });
  if(!judgments.length)throw new Error('Choose a usefulness judgment for at least one packet.');
  return {version:'m7-human-usefulness-v1',package_sha256:packageHash,result_sha256:pkg.result_sha256,
    bundle_sha256:pkg.bundle_sha256,reviewer:reviewer.trim(),attribution:'self_reported_human',
    recorded_at:new Date().toISOString(),judgments,unreviewed_slots:pkg.items.filter(i=>!feedback[i.slot]?.usefulness).map(i=>i.slot),
    analyst_acceptance:null,time_saved_seconds:null,promotions:0};
}

export function safeSourceUrl(value:string):string|null{
  try{const url=new URL(value);return ['http:','https:'].includes(url.protocol)&&!url.username&&!url.password?url.href:null}catch{return null}
}
