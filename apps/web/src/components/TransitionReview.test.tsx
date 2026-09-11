import {render,screen} from '@testing-library/react';
import {describe,expect,it} from 'vitest';
import {TransitionReview,TransitionReviewItem} from './TransitionReview';

const item:TransitionReviewItem={claim_id:1,evidence_id:2,signal_type:'retirement',subject_type:'person',person:'Jordan Example',business:'Fictional Business',event_date:null,event_status:'planned',publication_date:'2026-09-01T00:00:00Z',retrieved_at:'2026-09-02T00:00:00Z',publisher:'Fictional News',canonical_url:'https://example.test/story',classification:'source_fact',claim_status:'asserted',policy_version:'transition-policy-v1',policy:{label:'Retirement',evidence_requirements:['Retain the role statement.'],temporal_questions:['When does retirement take effect?'],ownership_limitations:['Retirement does not establish an ownership exit.'],review_questions:['Does the person retain control?']},uncertainties:['Event date is unknown; publication date is not a substitute.']};

describe('TransitionReview',()=>{
  it('keeps unknown event timing, evidence and guidance distinct',()=>{
    render(<TransitionReview items={[item]}/>);
    expect(screen.getByText('Unknown')).toBeInTheDocument();
    expect(screen.getByText('planned')).toBeInTheDocument();
    expect(screen.getByText(/does not establish an ownership exit/)).toBeInTheDocument();
    expect(screen.getByText(/publication date is not a substitute/)).toBeInTheDocument();
    expect(screen.getByRole('link',{name:/Fictional News/})).toHaveAttribute('href','https://example.test/story');
    expect(screen.getByText(/Research guidance/)).toBeInTheDocument();
  });
  it('keeps unsupported clues visible and refuses unsafe source links',()=>{
    render(<TransitionReview items={[{...item,policy:null,canonical_url:'javascript:alert(1)'}]}/>);
    expect(screen.getByText(/Keep this clue in research/)).toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });
});
