import {afterEach,expect,it,vi} from 'vitest';
import {api} from './client';

afterEach(()=>vi.unstubAllGlobals());

it('adds the same-origin signal only to mutation requests',async()=>{
  const fetchMock=vi.fn().mockImplementation(()=>Promise.resolve(new Response(JSON.stringify({ok:true}),{status:200,headers:{'Content-Type':'application/json'}})));
  vi.stubGlobal('fetch',fetchMock);
  await api('/health');
  await api('/saved-research',{method:'POST',body:'{}'});
  const readHeaders=fetchMock.mock.calls[0][1].headers as Headers;
  const mutationHeaders=fetchMock.mock.calls[1][1].headers as Headers;
  expect(readHeaders.get('X-DealSage-CSRF')).toBeNull();
  expect(mutationHeaders.get('X-DealSage-CSRF')).toBe('1');
});
