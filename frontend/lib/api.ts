const API=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000/api';
async function req(path:string,init?:RequestInit){const r=await fetch(`${API}${path}`,{...init,headers:{'Content-Type':'application/json',...(init?.headers||{})}});const data=await r.json().catch(()=>({detail:'Invalid server response'}));if(!r.ok)throw new Error(data.detail||'Request failed');return data}
export const api={
 dashboard:()=>req('/dashboard'), interviews:()=>req('/interviews'), interview:(id:number)=>req(`/interviews/${id}`), feedback:(id:number)=>req(`/interviews/${id}/feedback`),
 demo:()=>req('/resume/demo',{method:'POST'}),
 upload:async(file:File)=>{const fd=new FormData();fd.append('file',file);const r=await fetch(`${API}/resume/upload`,{method:'POST',body:fd});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Upload failed');return d},
 create:(body:any)=>req('/interviews',{method:'POST',body:JSON.stringify(body)}), start:(id:number)=>req(`/interviews/${id}/start`,{method:'POST'}),
 answer:(id:number,body:any)=>req(`/interviews/${id}/answer`,{method:'POST',body:JSON.stringify(body)}), next:(id:number)=>req(`/interviews/${id}/next-question`,{method:'POST'}), complete:(id:number)=>req(`/interviews/${id}/complete`,{method:'POST'}),
 delete:(id:number)=>req(`/interviews/${id}`,{method:'DELETE'})
};
