import {render,screen} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {describe,expect,it,vi} from 'vitest';
import {Research} from './Research';
import {MemoryRouter} from 'react-router-dom';
import fixtures from '../test/businessBriefFixture.json';
vi.mock('../api/client',()=>({api:vi.fn(async(path:string)=>{
  if(path==='/research/case-narratives')return {cases:fixtures};
  throw new Error('Historical experiment unavailable');
})}));
describe('Research',()=>{
  it('renders business briefs when unrelated historical queries fail',async()=>{
    const client=new QueryClient({defaultOptions:{queries:{retry:false}}});
    render(<QueryClientProvider client={client}><MemoryRouter><Research/></MemoryRouter></QueryClientProvider>);
    expect(await screen.findByRole('heading',{name:'Summit Tool Works'})).toBeVisible();
    expect(await screen.findByText('Source operations and historical experiments')).toBeVisible();
    expect(screen.getByRole('link',{name:/record usefulness feedback/})).toBeVisible();
  });
});
