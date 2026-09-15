import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter} from 'react-router-dom';
import {CaseFollowups} from './CaseFollowups';
vi.mock('./AuthGate',()=>({useIdentity:()=>({role:'analyst'})}));
afterEach(()=>{cleanup();vi.unstubAllGlobals()});
it('invalidates a frozen preview when the reviewer edits the query',async()=>{
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>new Response(JSON.stringify(url.endsWith('/preview')?{hash:'a'.repeat(64),plan:{submitted_queries:['Fictional search'],provider:{reason:'Fictional offline provider',reservation_cents:0},settings:{max_records:10}}}:{items:[]}))));
  render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><MemoryRouter><CaseFollowups caseId={1}/></MemoryRouter></QueryClientProvider>);
  fireEvent.change(screen.getByLabelText('Follow-up question'),{target:{value:'Is the business operating?'}});
  fireEvent.change(screen.getByLabelText('Why this needs research'),{target:{value:'Operating status is unknown'}});
  fireEvent.change(screen.getByLabelText('Exact search query'),{target:{value:'Fictional Acme operating'}});
  fireEvent.click(screen.getByRole('button',{name:'Preview follow-up'}));
  expect(await screen.findByRole('button',{name:'Save follow-up plan'})).toBeVisible();
  expect(screen.getByText(/Finding a link does not answer/)).toBeVisible();
  fireEvent.change(screen.getByLabelText('Exact search query'),{target:{value:'A revised fictional query'}});
  expect(screen.queryByRole('button',{name:'Save follow-up plan'})).toBeNull();
});
