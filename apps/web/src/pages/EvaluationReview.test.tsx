import {fireEvent,render,screen,waitFor,cleanup} from '@testing-library/react';
import {afterEach,describe,expect,it,vi} from 'vitest';
import {EvaluationReview} from './EvaluationReview';
import {feedbackRecord,parseReviewPackage,safeSourceUrl} from '../evaluationReview';
import {evaluationFixture as fixture} from '../test/evaluationFixture';

afterEach(()=>{cleanup();vi.unstubAllGlobals()});
describe('local evaluation review',()=>{
  it('preserves unknown judgments and optional time, binding feedback to exact package',()=>{
    const pkg=structuredClone(fixture);pkg.items.push({...pkg.items[0],slot:'SECOND'});
    const result=feedbackRecord(pkg,'c'.repeat(64),'Reviewer',{'FICTIONAL-CO-1':{usefulness:'useful',rationale:'Useful questions',review_minutes:''}});
    expect(result.package_sha256).toBe('c'.repeat(64));expect(result.unreviewed_slots).toEqual(['SECOND']);
    expect(result.judgments[0].self_reported_review_seconds).toBeNull();expect(result.time_saved_seconds).toBeNull();
    expect(result.analyst_acceptance).toBeNull();expect(result.promotions).toBe(0);
    expect(pkg.items[0].model_dimensions.operating_status).toBe('active');
  });
  it('requires explicit judgment and rationale without inventing a human review',()=>{
    expect(()=>feedbackRecord(fixture,'c'.repeat(64),'Reviewer',{})).toThrow(/Choose/);
    expect(()=>feedbackRecord(fixture,'c'.repeat(64),'Reviewer',{'FICTIONAL-CO-1':{usefulness:'defer',rationale:'',review_minutes:'1'}})).toThrow(/rationale/);
    expect(()=>feedbackRecord(fixture,'c'.repeat(64),'Reviewer',{'FICTIONAL-CO-1':{usefulness:'useful',rationale:'Useful clues',review_minutes:'-1'}})).toThrow(/minutes/);
    const result=feedbackRecord(fixture,'c'.repeat(64),'Reviewer',{'FICTIONAL-CO-1':{usefulness:'defer',rationale:'Need more evidence',review_minutes:'1.5'}});
    expect(result.judgments[0].self_reported_review_seconds).toBe(90);
  });
  it('rejects malformed, duplicated and missing-citation packages',()=>{
    expect(()=>parseReviewPackage('null')).toThrow(/Unsupported/);
    const duplicate=structuredClone(fixture);duplicate.items.push(duplicate.items[0]);
    expect(()=>parseReviewPackage(JSON.stringify(duplicate))).toThrow(/distinct/);
    const missing=structuredClone(fixture);missing.items[0].supported_source_ids=['missing'];
    expect(()=>parseReviewPackage(JSON.stringify(missing))).toThrow(/missing/);
    expect(()=>parseReviewPackage('x'.repeat(2_000_001))).toThrow(/limit/);
  });
  it('allows only ordinary web source links',()=>{
    expect(safeSourceUrl('javascript:alert(1)')).toBeNull();expect(safeSourceUrl('https://user:secret@example.test')).toBeNull();
    expect(safeSourceUrl('https://example.test/source')).toBe('https://example.test/source');
  });
  it('renders evidence as text, separates original and contextual labels, and never uploads',async()=>{
    vi.stubGlobal('crypto',{subtle:{digest:vi.fn(async()=>new Uint8Array(32).buffer)}});const fetch=vi.fn();vi.stubGlobal('fetch',fetch);
    render(<EvaluationReview/>);
    const bytes=new TextEncoder().encode(JSON.stringify(fixture));
    const file=new File([bytes],'fictional.json',{type:'application/json'});
    Object.defineProperty(file,'arrayBuffer',{value:async()=>bytes.buffer});
    fireEvent.change(screen.getByLabelText('Review package (.json)'),{target:{files:[file]}});
    await screen.findByText('1 packets loaded');
    expect(crypto.subtle.digest).toHaveBeenCalledWith('SHA-256',bytes.buffer);
    expect(screen.getByText('Fictional Alpine Works announced management succession. Executive ownership remains unestablished.')).toBeInTheDocument();
    expect(screen.getByText('active')).toBeInTheDocument();expect(screen.getAllByText('unknown').length).toBeGreaterThan(0);
    expect(screen.getByText(/<img src=x/)).toBeInTheDocument();expect(document.querySelector('img')).toBeNull();
    expect(screen.queryByRole('link',{name:'Open original source'})).toBeNull();
    expect(screen.getByLabelText('Usefulness for FICTIONAL-CO-1')).toHaveValue('');
    expect(fetch).not.toHaveBeenCalled();
    const broken=new File(['bad'],'broken.json');Object.defineProperty(broken,'arrayBuffer',{value:async()=>new TextEncoder().encode('bad').buffer});
    fireEvent.change(screen.getByLabelText('Review package (.json)'),{target:{files:[broken]}});
    await waitFor(()=>expect(screen.getByRole('alert')).toBeInTheDocument());
    expect(screen.queryByText('Download feedback JSON')).toBeNull();
  });
});
