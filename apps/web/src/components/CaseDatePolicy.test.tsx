import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {CaseDatePolicy} from './CaseDatePolicy';
vi.mock('./AuthGate',()=>({useIdentity:()=>({role:'analyst'})}));
afterEach(()=>{cleanup();vi.unstubAllGlobals()});
it('requires explicit review and reuses the same renewal after a lost response',async()=>{
  const posts:string[]=[];
  const fetcher=vi.fn(async(_url:string,options?:RequestInit)=>{
    if(options?.method==='POST'){posts.push(options.body as string);throw new Error('Response lost')}
    return new Response(JSON.stringify({before:{assessment_date:'2026-01-01',lookback_days:90},after:{assessment_date:'2026-09-15',lookback_days:90},hash:'abc',changed:true,history:[],has_next:false}));
  });vi.stubGlobal('fetch',fetcher);
  render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><CaseDatePolicy caseId={1}/></QueryClientProvider>);
  expect(fetcher).not.toHaveBeenCalled();fireEvent.click(screen.getByRole('button',{name:'Review research date window'}));
  fireEvent.change(await screen.findByLabelText('Reason for renewing date window'),{target:{value:'Review the current date window explicitly.'}});
  fireEvent.click(screen.getByRole('button',{name:'Confirm date-window renewal'}));
  fireEvent.click(await screen.findByRole('button',{name:'Retry same renewal'}));
  await waitFor(()=>expect(posts).toHaveLength(2));expect(posts[0]).toBe(posts[1]);
  expect(screen.getByText(/does not make old evidence recent/)).toBeVisible();
});
