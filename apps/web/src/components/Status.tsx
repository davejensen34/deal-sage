export function Status({value}:{value:string}){return <span className={`status status-${value}`}>{value.replace('_',' ')}</span>}
export function Score({value,label}:{value:number;label?:string}){const tone=value>=80?'high':value>=60?'medium':'low';return <div className={`score ${tone}`}><b>{value}%</b>{label&&<span>{label}</span>}</div>}
export const fmt=(v:string)=>new Date(v).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});
