import {render,screen,within,fireEvent} from '@testing-library/react';
import {describe,expect,it} from 'vitest';
import {CaseNarratives,CaseNarrative} from './CaseNarratives';
import {BusinessBrief,sourceLink} from './BusinessBrief';
import fixtures from '../test/businessBriefFixture.json';

const cases=fixtures as CaseNarrative[];
describe('Business research briefs',()=>{
  it('leads with recent businesses and keeps all five cases visible',()=>{
    const {container}=render(<CaseNarratives cases={cases}/>);
    const headings=[...container.querySelectorAll('.brief-heading h3')].map(h=>h.textContent);
    expect(headings.slice(0,2)).toEqual(expect.arrayContaining(['Summit Tool Works','Mesa Services']));
    expect(headings).toHaveLength(5);
    expect(screen.getByText('Historical background')).toBeVisible();
    expect(screen.getByText('Future plan')).toBeVisible();
    expect(screen.getByText(/outside the current private-company acquisition focus/)).toBeVisible();
    expect(screen.getAllByText(/second retained claim/)[0]).toBeVisible();
  });
  it('attributes size and preserves unknown financials without making ownership claims',()=>{
    const item=cases.find(c=>c.lead_brief!.title==='Summit Tool Works')!;
    render(<BusinessBrief brief={item.lead_brief!} evidence={item.evidence}/>);
    expect(screen.getByText('24, reported by company',{exact:false})).toBeVisible();
    expect(screen.getAllByText('Unknown',{exact:false})).toHaveLength(2);
    expect(screen.getByText(/does not establish ownership/)).toBeVisible();
    expect(screen.getAllByRole('link').every(a=>a.getAttribute('href')?.startsWith('https://example.test/'))).toBe(true);
    fireEvent.click(screen.getByText(/Read the transition source/));
    expect(screen.getByText(/Fictional fixture:/)).toBeVisible();
  });
  it('renders untrusted text literally and refuses credential-bearing or executable links',()=>{
    const item=structuredClone(cases[0]);
    item.lead_brief!.title='<img src=x onerror=alert(1)>';
    item.lead_brief!.facts[0].url='javascript:alert(1)';
    const {container}=render(<BusinessBrief brief={item.lead_brief!} evidence={item.evidence}/>);
    expect(screen.getByRole('heading',{name:'<img src=x onerror=alert(1)>'})).toBeVisible();
    expect(container.querySelector('img')).toBeNull();
    expect(sourceLink('https://user:password@example.test')).toBeUndefined();
    expect(sourceLink('javascript:alert(1)')).toBeUndefined();
    expect(sourceLink('https://example.test/path')).toBe('https://example.test/path');
  });
  it('keeps detailed review available without dominating the brief',()=>{
    const {container}=render(<CaseNarratives cases={cases}/>);
    const review=container.querySelector('.case-review') as HTMLDetailsElement;
    expect(review.open).toBe(false);
    fireEvent.click(within(review).getByText(/Evidence, models and analyst review/));
    expect(review.open).toBe(true);
  });
});
