import {afterEach, expect, it, vi} from 'vitest';
import {cleanup, fireEvent, render, screen} from '@testing-library/react';
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter, Route, Routes} from 'react-router-dom';
import {Shell} from './Shell';

vi.mock('./AuthGate',()=>({useIdentity:()=>({role:'viewer',provider:'google',display_name:'Example reviewer',email:'reviewer@example.test'})}));
afterEach(()=>{cleanup();vi.unstubAllGlobals()});
it('signs out through the CSRF-protected endpoint and clears cached research',async()=>{
  const fetcher=vi.fn(async()=>new Response(JSON.stringify({status:'signed_out'})));
  vi.stubGlobal('fetch',fetcher);
  const client=new QueryClient();client.setQueryData(['private-research'],{case:1});
  render(<QueryClientProvider client={client}><MemoryRouter><Routes><Route path="/" element={<Shell/>}/><Route path="/login" element={<h1>Sign in</h1>}/></Routes></MemoryRouter></QueryClientProvider>);
  fireEvent.click(screen.getByRole('button',{name:'Sign out'}));
  expect(await screen.findByRole('heading',{name:'Sign in'})).toBeVisible();
  expect(fetcher).toHaveBeenCalledWith('/api/auth/logout',expect.objectContaining({method:'POST'}));
  expect(client.getQueryData(['private-research'])).toBeUndefined();
});
