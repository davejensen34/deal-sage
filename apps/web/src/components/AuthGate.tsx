import {createContext,useContext} from 'react';
import {useQuery} from '@tanstack/react-query';
import {Navigate} from 'react-router-dom';
import {api} from '../api/client';

export type Identity={user_id:number|null;provider:string;subject:string;email:string|null;display_name:string;avatar_url:string|null};
const IdentityContext=createContext<Identity|null>(null);
export const useIdentity=()=>useContext(IdentityContext);

export function AuthGate({children}:{children:React.ReactNode}){const identity=useQuery({queryKey:['identity'],queryFn:()=>api<Identity>('/auth/me'),retry:false});if(identity.isLoading)return <div className="auth-loading">Opening DealSage…</div>;if(identity.isError||!identity.data)return <Navigate to="/login" replace/>;return <IdentityContext.Provider value={identity.data}>{children}</IdentityContext.Provider>}
